#!/usr/bin/env python3
"""
Background worker for processing brand influencer sync jobs.
Polls Azure Queue, runs sync script, moves failures to DLQ.

Usage:
    python scripts/worker.py
"""
import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime
from azure.storage.queue import QueueClient, TextBase64DecodePolicy
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Configuration from environment
CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
QUEUE_NAME = os.getenv("ADD_BRAND_INFL_QUEUE_NAME", "add-brand-infl")
DLQ_NAME = os.getenv("ADD_BRAND_INFL_DLQ_NAME", "add-brand-infl-dlq")
VISIBILITY_TIMEOUT = int(os.getenv("ADD_BRAND_INFL_WORKER_VISIBILITY_TIMEOUT", "43200"))
POLL_WAIT_TIME = int(os.getenv("ADD_BRAND_INFL_WORKER_POLL_WAIT_TIME", "30"))
SLEEP_ON_EMPTY = int(os.getenv("ADD_BRAND_INFL_WORKER_SLEEP_ON_EMPTY", "5"))


def get_queue_client(queue_name: str) -> QueueClient:
    """Get Azure Queue client."""
    if CONNECTION_STRING:
        return QueueClient.from_connection_string(
            CONNECTION_STRING, 
            queue_name=queue_name,
            message_decode_policy=TextBase64DecodePolicy()
        )
    elif STORAGE_ACCOUNT_NAME and STORAGE_ACCOUNT_KEY:
        account_url = f"https://{STORAGE_ACCOUNT_NAME}.queue.core.windows.net"
        return QueueClient(
            account_url=account_url, 
            credential=STORAGE_ACCOUNT_KEY, 
            queue_name=queue_name,
            message_decode_policy=TextBase64DecodePolicy()
        )
    else:
        raise ValueError("Azure Storage not configured. Set AZURE_STORAGE_CONNECTION_STRING or both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY.")


def process_job(message_data: dict, queue_client: QueueClient, dlq_client: QueueClient):
    """Process a single job - run sync script."""
    job_id = message_data.get("job_id", "unknown")
    brand = message_data.get("brand")

    logger.info(f"Processing job {job_id}: brand=@{brand}")

    # Get sync script path (relative to project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sync_script = os.path.join(os.path.dirname(script_dir), "scripts", "sync_brand_influencers.py")

    # Run sync script
    try:
        result = subprocess.run(
            [sys.executable, sync_script, "--brand", brand,
             "--max-posts", str(message_data.get("max_posts", 10000)),
             "--max-api-calls", str(message_data.get("max_api_calls", 500))],
            timeout=VISIBILITY_TIMEOUT - 60
        )

        if result.returncode == 0:
            logger.info(f"Success: job {job_id} completed for @{brand}")
        else:
            logger.error(f"Failed: job {job_id} for @{brand}")

            # Send to DLQ
            dlq_payload = {
                **message_data,
                "error": f"Script failed with exit code {result.returncode}",
                "failed_at": datetime.now().isoformat()
            }
            dlq_client.send_message(json.dumps(dlq_payload))
            logger.warning(f"Moved job {job_id} to DLQ")

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout: job {job_id} for @{brand} exceeded visibility timeout")
        dlq_payload = {
            **message_data,
            "error": "Timeout: exceeded visibility timeout",
            "failed_at": datetime.now().isoformat()
        }
        dlq_client.send_message(json.dumps(dlq_payload))

    except Exception as e:
        logger.error(f"Exception: job {job_id} for @{brand}: {e}")
        dlq_payload = {
            **message_data,
            "error": str(e)[:500],
            "failed_at": datetime.now().isoformat()
        }
        dlq_client.send_message(json.dumps(dlq_payload))


def main():
    """Main worker loop."""
    logger.info(f"Worker starting...")
    logger.info(f"Queue: {QUEUE_NAME}")
    logger.info(f"DLQ: {DLQ_NAME}")
    logger.info(f"Visibility timeout: {VISIBILITY_TIMEOUT}s ({VISIBILITY_TIMEOUT/3600}h)")
    logger.info(f"Poll wait: {POLL_WAIT_TIME}s")

    queue = get_queue_client(QUEUE_NAME)
    dlq = get_queue_client(DLQ_NAME)

    logger.info("Worker ready")

    while True:
        try:
            # Poll for messages
            messages = queue.receive_messages(
                max_messages=1,
                visibility_timeout=VISIBILITY_TIMEOUT,
                timeout=POLL_WAIT_TIME
            )

            # Convert to list to check if any messages
            msg_list = list(messages)
            
            if not msg_list:
                time.sleep(SLEEP_ON_EMPTY)
                continue

            for msg in msg_list:
                content = msg.content
                
                # Skip empty messages
                if not content:
                    queue.delete_message(msg.id, msg.pop_receipt)
                    continue
                
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                
                # Skip empty content after decode
                if not content:
                    queue.delete_message(msg.id, msg.pop_receipt)
                    continue
                
                message_data = json.loads(content)

                # Process the job
                process_job(message_data, queue, dlq)

                # Delete from main queue
                queue.delete_message(msg.id, msg.pop_receipt)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(SLEEP_ON_EMPTY)


if __name__ == "__main__":
    main()