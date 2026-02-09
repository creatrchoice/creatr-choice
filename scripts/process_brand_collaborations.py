#!/usr/bin/env python3
"""
Process brand collaborations from config file.
For each influencer entry, check if they exist in DB, check if collab already exists,
and create new collaboration if conditions are met.
"""
import argparse
import json
import logging
import os
import sys
import re
from datetime import datetime, timezone
from typing import Optional, Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
CONFIG_PATH = os.getenv("CONFIG_PATH", "app/config/free-infl-copy.json")

BRAND_ID_MAP = {
    "dot & key": "dot_and_key",
    "tira beauty": "tira_beauty",
}

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
RESULTS_FILE = f"run-results/run-{timestamp}.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/process_brand_collaborations.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def normalize_brand_id(raw_brand_id: str) -> str:
    """Normalize brand_id using hardcoded mapping or fallback to original."""
    return BRAND_ID_MAP.get(raw_brand_id, raw_brand_id)


def extract_username(instagram_handle: str) -> str:
    """Extract username from Instagram handle URL."""
    if not instagram_handle:
        return ""
    match = re.search(r'(?:instagram|instagam)\.com/([^/]+)', instagram_handle)
    if match:
        return match.group(1)
    return instagram_handle.strip("/")


def load_config(path: str) -> list:
    """Load influencer entries from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("influencers", [])


def check_influencer_exists(username: str) -> Optional[dict]:
    """Check if influencer exists in DB via GET API."""
    try:
        response = requests.get(
            f"{BASE_URL}/free-influencers/",
            params={"username": username, "platform": "instagram"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("count", 0) > 0:
                logger.info(f"[EXISTS] @{username} found in DB")
                return data["data"][0]
        logger.info(f"[NOT FOUND] @{username} not in DB")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Check influencer failed for @{username}: {e}")
        return None


def check_collaboration_exists(brand_id: str, influencer_id: str) -> bool:
    """Check if collaboration already exists."""
    try:
        response = requests.get(
            f"{BASE_URL}/brand-collaborations",
            params={"brand_id": brand_id, "influencer_id": influencer_id},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("count", 0) > 0:
                return True
        return False
    except Exception as e:
        logger.error(f"[ERROR] Check collab failed for brand={brand_id}, infl={influencer_id}: {e}")
        return False


def create_collaboration(data: dict) -> tuple[Optional[dict], bool]:
    """Create collaboration via POST API. Returns (response_data, success)."""
    try:
        response = requests.post(
            f"{BASE_URL}/brand-collaborations/",
            json=data,
            timeout=10
        )
        if response.status_code == 201:
            logger.info(f"[CREATED] Collab: brand={data['brand_id']}, infl={data['influencer_id']}")
            return response.json(), True
        else:
            logger.error(f"[ERROR] Create collab failed: HTTP {response.status_code}")
            logger.error(f"[ERROR] Response: {response.text[:500]}")
            return None, False
    except Exception as e:
        logger.error(f"[ERROR] Create collab exception: {e}")
        return None, False


def validate_collaboration_data(data: dict, raw_brand_id: str) -> tuple[bool, str]:
    """Validate collaboration data. Returns (is_valid, concern_message)."""
    if not data.get("brand_id"):
        return False, f"Missing brand_id (raw: {raw_brand_id})"
    if not data.get("influencer_id"):
        return False, "Missing influencer_id"
    try:
        likes = int(data.get("likes", 0))
        comments = int(data.get("comments", 0))
        if likes < 0 or comments < 0:
            return False, "Negative likes or comments"
    except (ValueError, TypeError):
        return False, "Invalid likes/comments format"
    return True, ""


def save_json_file(filepath: str, data):
    """Save data to JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"[SAVED] {filepath}")
    except Exception as e:
        logger.error(f"[ERROR] Could not save {filepath}: {e}")


def process_influencer(infl_entry: dict, processed_count: dict) -> dict:
    """Process single influencer entry."""
    raw_brand_id = infl_entry.get("brand_id", "")
    
    username = infl_entry.get("username", "")
    if not username:
        username = extract_username(infl_entry.get("instagram_handle", ""))

    result = {
        "username": username,
        "raw_brand_id": raw_brand_id,
        "normalized_brand_id": None,
        "influencer_id": None,
        "collab_id": None,
        "status": "pending",
        "concern": None,
        "likes": infl_entry.get("likes", 0),
        "comments": infl_entry.get("comments", 0),
        "post_link": infl_entry.get("post_link", "")
    }

    if not username:
        result["status"] = "skipped"
        result["concern"] = "Missing username"
        return result

    normalized_brand_id = normalize_brand_id(raw_brand_id)
    result["normalized_brand_id"] = normalized_brand_id
    if raw_brand_id != normalized_brand_id:
        logger.info(f"[MAPPED] '{raw_brand_id}' -> '{normalized_brand_id}'")

    influencer = check_influencer_exists(username)
    if not influencer:
        result["status"] = "missing_influencer"
        processed_count["missing_influencers"] += 1
        return result

    result["influencer_id"] = influencer["id"]

    if check_collaboration_exists(normalized_brand_id, influencer["id"]):
        result["status"] = "skipped_existing"
        processed_count["skipped_existing"] += 1
        logger.info(f"[SKIPPED] Collab already exists: brand={normalized_brand_id}, infl={username}")
        return result

    collab_data = {
        "brand_id": normalized_brand_id,
        "influencer_id": influencer["id"],
        "likes": int(infl_entry.get("likes", 0)),
        "comments": int(infl_entry.get("comments", 0)),
        "captured_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "post_link": infl_entry.get("post_link", "") or None
    }

    is_valid, concern = validate_collaboration_data(collab_data, raw_brand_id)
    if not is_valid:
        result["status"] = "validation_failed"
        result["concern"] = concern
        processed_count["validation_failed"] += 1
        logger.warning(f"[VALIDATION] Failed: {concern}")
        return result

    collab, success = create_collaboration(collab_data)
    if success:
        result["collab_id"] = collab.get("id") if collab else None
        result["status"] = "created"
        processed_count["new_collaborations"] += 1
        processed_count["total_processed"] += 1
    else:
        result["status"] = "failed"
        processed_count["failed"] += 1
        processed_count["total_processed"] += 1

    return result


def main():
    parser = argparse.ArgumentParser(description="Process brand collaborations from JSON file")
    parser.add_argument("--test", action="store_true", help="Test with 1 influencer")
    parser.add_argument("--max", type=int, default=0, help="Max new collaborations to create (0=unlimited)")
    parser.add_argument("--config", type=str, default=CONFIG_PATH, help="Path to config JSON (legacy)")
    parser.add_argument("--file", type=str, required=True, help="Path to JSON file with influencer data")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting brand collaboration processor")
    logger.info(f"Input file: {args.file}")
    logger.info(f"Max new collaborations: {'unlimited' if args.max == 0 else args.max}")
    logger.info(f"Test mode: {args.test}")
    logger.info("=" * 60)

    if not os.path.exists(args.file):
        logger.error(f"[ERROR] File not found: {args.file}")
        return

    influencers = load_config(args.file)
    if args.test:
        influencers = influencers[:1]
        logger.info("[TEST] Running with 1 influencer")

    if not influencers:
        logger.warning("[EMPTY] No influencers found in config")
        return

    logger.info(f"Total influencers to process: {len(influencers)}")

    processed_count = {
        "total_processed": 0,
        "new_collaborations": 0,
        "skipped_existing": 0,
        "missing_influencers": 0,
        "validation_failed": 0,
        "failed": 0
    }
    results = []
    missing_influencers = []
    skipped_existing = []
    failed_collab = []

    for i, infl in enumerate(influencers):
        logger.info(f"[{i+1}/{len(influencers)}] Processing: @{infl.get('username', 'UNKNOWN')}")

        result = process_influencer(infl, processed_count)
        results.append(result)

        if result["status"] == "missing_influencer":
            missing_influencers.append({
                "username": result["username"],
                "brand_id": result["raw_brand_id"],
                "instagram_handle": infl.get("instagram_handle", "")
            })
        elif result["status"] == "skipped_existing":
            skipped_existing.append({
                "username": result["username"],
                "brand_id": result["normalized_brand_id"],
                "influencer_id": result["influencer_id"]
            })
        elif result["status"] in ("failed", "validation_failed"):
            failed_collab.append({
                "username": result["username"],
                "brand_id": result["normalized_brand_id"],
                "influencer_id": result["influencer_id"],
                "status": result["status"],
                "concern": result["concern"]
            })

        logger.info(f"[STATS] New: {processed_count['new_collaborations']}, "
                   f"Skipped: {processed_count['skipped_existing']}, "
                   f"Missing: {processed_count['missing_influencers']}, "
                   f"Failed: {processed_count['failed']}")

        if args.max > 0 and processed_count["new_collaborations"] >= args.max:
            logger.info(f"[LIMIT] Reached max new collaborations ({args.max})")
            break

    stats = {
        "completed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "config_file": args.config,
        "max_new_collaborations": args.max if args.max > 0 else "unlimited",
        "total_influencers_in_config": len(influencers),
        "total_processed": processed_count["total_processed"],
        "new_collaborations_created": processed_count["new_collaborations"],
        "skipped_existing": processed_count["skipped_existing"],
        "missing_influencers": processed_count["missing_influencers"],
        "validation_failed": processed_count["validation_failed"],
        "failed": processed_count["failed"]
    }

    output = {
        "stats": stats,
        "results": results,
        "missing_influencers": missing_influencers,
        "skipped_existing": skipped_existing,
        "failed_collab": failed_collab
    }

    os.makedirs("run-results", exist_ok=True)
    with open(RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info("=" * 60)
    logger.info("Processing complete")
    logger.info(f"New collaborations: {processed_count['new_collaborations']}")
    logger.info(f"Skipped (existing): {processed_count['skipped_existing']}")
    logger.info(f"Missing influencers: {processed_count['missing_influencers']}")
    logger.info(f"Failed: {processed_count['failed']}")
    logger.info(f"Results saved to: {RESULTS_FILE}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
