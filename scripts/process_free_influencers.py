#!/usr/bin/env python3
"""
Process free influencers from config file.
Check if exists in DB, fetch from RapidAPI if not, save to DB.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
CONFIG_PATH = os.getenv("CONFIG_PATH", "app/config/free-infl-backup.json")

timestamp = datetime.now().strftime('%Y%m%d_%H%M')
RESULTS_FILE = f"run-results/run-{timestamp}.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/process_free_influencers.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config(path: str) -> list:
    """Load influencer entries from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("influencers", [])


def check_exists(username: str) -> Optional[dict]:
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
                logger.info(f"[EXISTS] @{username} already in DB")
                return data["data"][0]
        return None
    except Exception as e:
        logger.error(f"[ERROR] Check exists failed for @{username}: {e}")
        return None


def fetch_profile(username: str, retries: int = 1) -> Optional[dict]:
    """Fetch Instagram profile from RapidAPI with retry."""
    for attempt in range(retries + 1):
        try:
            logger.info(f"[RAPIDAPI] Fetching profile for @{username} (attempt {attempt + 1}/{retries + 1})")
            response = requests.post(
                "https://instagram120.p.rapidapi.com/api/instagram/profile",
                json={"username": username},
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": "instagram120.p.rapidapi.com",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            if response.status_code == 200:
                profile = response.json().get("result", {})
                if profile:
                    logger.info(f"[RAPIDAPI] Success for @{username}")
                    return profile
            else:
                logger.warning(f"[RAPIDAPI] HTTP {response.status_code} for @{username}")
        except Exception as e:
            logger.warning(f"[RAPIDAPI] Error for @{username}: {e}")

        if attempt < retries:
            sleep_time = 2 ** attempt
            logger.info(f"[RAPIDAPI] Retrying @{username} in {sleep_time}s...")
            time.sleep(sleep_time)

    logger.error(f"[RAPIDAPI] Failed after {retries + 1} attempts for @{username}")
    return None


def build_influencer_data(profile: dict, json_data: dict) -> dict:
    """Build influencer data object for API."""
    bio = profile.get("biography", "") or ""
    import re
    import regex
    try:
        bio = regex.sub(
            r"[\p{Extended_Pictographic}\p{Emoji_Presentation}\p{Symbol}]",
            "",
            bio,
            flags=regex.UNICODE
        )
        bio = re.sub(r"\s+", " ", bio).strip()
    except Exception:
        pass

    return {
        "id": str(profile.get("id")) if profile.get("id") else None,
        "platform": "instagram",
        "platform_user_id": str(profile.get("id")) if profile.get("id") else None,
        "username": profile.get("username", ""),
        "full_name": profile.get("full_name") or json_data.get("full_name", "") or json_data.get("username", ""),
        "bio": bio if bio else None,
        "is_private": profile.get("is_private", False),
        "followers": profile.get("edge_followed_by", {}).get("count", 0),
        "following": profile.get("edge_follow", {}).get("count", 0),
        "post_count": profile.get("edge_owner_to_timeline_media", {}).get("count", 0),
        "profile_image": {
            "url": profile.get("profile_pic_url", ""),
            "hd": profile.get("profile_pic_url_hd", "")
        },
        "last_fetched_at": datetime.utcnow().isoformat()
    }


def create_influencer(data: dict) -> tuple[Optional[dict], bool]:
    """Save influencer to DB via POST API.
    Returns (influencer_data, is_new) tuple."""
    try:
        response = requests.post(
            f"{BASE_URL}/free-influencers/",
            json=data,
            timeout=10
        )
        if response.status_code == 201:
            logger.info(f"[CREATED] @{data['username']} saved to DB")
            return response.json(), True
        elif response.status_code in (400, 409) and "Conflict" in response.text:
            logger.info(f"[EXISTS] @{data['username']} already in DB (Conflict)")
            return {"id": data["id"], "username": data["username"]}, False
        else:
            logger.error(f"[ERROR] Failed to create @{data['username']}: HTTP {response.status_code}")
            logger.error(f"[ERROR] Response: {response.text[:500]}")
            return None, False
    except Exception as e:
        logger.error(f"[ERROR] Create failed for @{data['username']}: {e}")
        return None, False


def save_failed_entry(username: str, json_data: dict, failed_entries: list):
    """Save failed entry to list."""
    failed_entries.append({
        "username": username,
        "json_data": json_data,
        "failed_at": datetime.utcnow().isoformat()
    })
    logger.info(f"[FAILED] @{username} added to failed entries")


def process_influencer(username: str, json_data: dict, max_api_calls: int, api_calls_made: int, failed_entries: list) -> dict:
    """Process single influencer."""
    result = {
        "username": username,
        "influencer_id": None,
        "brand_id": json_data.get("brand_id", ""),
        "collab_metrics": {
            "likes": int(json_data.get("likes", 0)),
            "comments": int(json_data.get("comments", 0)),
            "captured_at": datetime.utcnow().isoformat(),
            "post_link": json_data.get("post_link", "")
        },
        "status": "pending",
        "api_calls_made": api_calls_made
    }

    existing = check_exists(username)
    if existing:
        result["influencer_id"] = existing["id"]
        result["status"] = "existing"
        return result

    if api_calls_made >= max_api_calls:
        logger.warning(f"[LIMIT] Max API calls reached ({max_api_calls}), skipping @{username}")
        result["status"] = "skipped_limit"
        return result

    profile = fetch_profile(username, retries=2)
    if not profile:
        result["status"] = "failed_fetch"
        save_failed_entry(username, json_data, failed_entries)
        return result

    result["api_calls_made"] = api_calls_made + 1

    influencer_data = build_influencer_data(profile, json_data)
    if not influencer_data.get("id"):
        logger.error(f"[ERROR] No ID in profile for @{username}")
        result["status"] = "failed_no_id"
        save_failed_entry(username, json_data, failed_entries)
        return result

    saved, is_new = create_influencer(influencer_data)
    if not saved:
        result["status"] = "failed_create"
        save_failed_entry(username, json_data, failed_entries)
        return result

    result["influencer_id"] = saved["id"]
    result["status"] = "new" if is_new else "existing"
    return result


def main():
    parser = argparse.ArgumentParser(description="Process free influencers from JSON file")
    parser.add_argument("--max", type=int, default=0, help="Max RapidAPI calls (0=unlimited)")
    parser.add_argument("--config", type=str, default=CONFIG_PATH, help="Path to config JSON (legacy)")
    parser.add_argument("--file", type=str, required=True, help="Path to JSON file with influencer data")
    parser.add_argument("--test", action="store_true", help="Test with 1 influencer")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("Starting free influencer processor")
    logger.info(f"Input file: {args.file}")
    logger.info(f"Max API calls: {'unlimited' if args.max == 0 else args.max}")
    logger.info("=" * 50)

    if not os.path.exists(args.file):
        logger.error(f"[ERROR] File not found: {args.file}")
        return

    influencers = load_config(args.file)
    if args.test:
        influencers = influencers[:1]
        logger.info("[TEST] Running with 1 influencer")

    logger.info(f"Total influencers to process: {len(influencers)}")

    counters = {
        "total": 0,
        "existing": 0,
        "new": 0,
        "errors": 0,
        "api_calls_made": 0,
        "skipped": 0
    }
    results = []
    failed_entries = []

    for i, infl in enumerate(influencers):
        username = infl.get("username", "")
        if not username:
            continue

        counters["total"] += 1
        logger.info(f"[{i+1}/{len(influencers)}] Processing @{username}")

        result = process_influencer(
            username, infl, args.max, counters["api_calls_made"], failed_entries
        )
        results.append(result)

        if result["status"] == "existing":
            counters["existing"] += 1
            counters["api_calls_made"] = result["api_calls_made"]
        elif result["status"] == "new":
            counters["new"] += 1
            counters["api_calls_made"] = result["api_calls_made"]
        elif result["status"] in ("failed_fetch", "failed_create", "failed_no_id"):
            counters["errors"] += 1
        elif result["status"] == "skipped_limit":
            counters["skipped"] += 1
            logger.warning(f"[LIMIT] Stopping - max API calls reached")
            break

        logger.info(f"[STATS] Processed: {counters['total']}, New: {counters['new']}, "
                   f"Existing: {counters['existing']}, Errors: {counters['errors']}, "
                   f"API calls: {counters['api_calls_made']}/{args.max}")

    stats = {
        "completed_at": datetime.utcnow().isoformat(),
        "total_processed": counters["total"],
        "existing_found": counters["existing"],
        "new_created": counters["new"],
        "errors": counters["errors"],
        "skipped": counters["skipped"],
        "api_calls_made": counters["api_calls_made"],
        "max_api_calls": args.max
    }

    output = {
        "stats": stats,
        "results": results,
        "failed_entries": failed_entries
    }

    os.makedirs("run-results", exist_ok=True)
    with open(RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info("=" * 50)
    logger.info("Processing complete")
    logger.info(f"Total processed: {counters['total']}")
    logger.info(f"Existing in DB: {counters['existing']}")
    logger.info(f"New created: {counters['new']}")
    logger.info(f"Errors: {counters['errors']}")
    logger.info(f"API calls made: {counters['api_calls_made']}/{args.max}")
    logger.info(f"Results saved to: {RESULTS_FILE}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
