"""Azure Queue service for add-brand-infl worker."""
import os
import json
import uuid
import logging
from azure.storage.queue import QueueClient, TextBase64EncodePolicy, TextBase64DecodePolicy
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class QueueService:
    """Service for interacting with Azure Storage Queues."""

    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.queue_name = os.getenv("ADD_BRAND_INFL_QUEUE_NAME", "add-brand-infl")
        self.dlq_name = os.getenv("ADD_BRAND_INFL_DLQ_NAME", "add-brand-infl-dlq")

        if not self.connection_string and not (self.account_name and self.account_key):
            raise ValueError("Azure Storage not configured. Set AZURE_STORAGE_CONNECTION_STRING or both AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY.")

    def _get_queue_client(self, queue_name: str) -> QueueClient:
        """Get queue client for specified queue."""
        if self.connection_string:
            return QueueClient.from_connection_string(
                self.connection_string, 
                queue_name=queue_name,
                message_encode_policy=TextBase64EncodePolicy(),
                message_decode_policy=TextBase64DecodePolicy()
            )
        else:
            account_url = f"https://{self.account_name}.queue.core.windows.net"
            return QueueClient(
                account_url=account_url, 
                credential=self.account_key, 
                queue_name=queue_name,
                message_encode_policy=TextBase64EncodePolicy(),
                message_decode_policy=TextBase64DecodePolicy()
            )

    def add_brand_job(self, brand: str, max_posts: int = 10000, max_api_calls: int = 500) -> str:
        """Add a new brand sync job to the queue."""
        job_id = str(uuid.uuid4())
        
        message = {
            "job_id": job_id,
            "brand": brand,
            "max_posts": max_posts,
            "max_api_calls": max_api_calls
        }

        queue_client = self._get_queue_client(self.queue_name)
        queue_client.send_message(json.dumps(message))

        logger.info(f"Added job {job_id} for brand @{brand}")
        return job_id


queue_service = QueueService()