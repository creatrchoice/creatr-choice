#!/usr/bin/env python3
"""
Unified brand pipeline: scrape brand posts, import influencers, create collaborations.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/brand_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def scrape_brand(brand: str, max_posts: int, max_api_calls: int) -> tuple[Optional[str], Optional[str]]:
    """
    Scrape brand posts via API. Returns (json_file_path, last_cursor).
    """
    logger.info(f"[SCRAPE] Starting scrape for @{brand}")
    logger.info(f"[SCRAPE] max_posts={max_posts}, max_api_calls={max_api_calls}")

    try:
        response = requests.post(
            f"{BASE_URL}/influencers/scrape",
            params={"json": "true"},
            json={
                "username": brand,
                "max_posts": max_posts,
                "max_api_calls": max_api_calls,
                "exclude_usernames": []
            },
            timeout=3600
        )

        if response.status_code != 200:
            logger.error(f"[SCRAPE] Failed with HTTP {response.status_code}: {response.text[:500]}")
            return None, None

        data = response.json()
        json_file_path = data.get("file_path")
        last_cursor = data.get("last_cursor")

        logger.info(f"[SCRAPE] Success - saved to {json_file_path}")
        logger.info(f"[SCRAPE] Found {data.get('influencer_count', 0)} influencers, last_cursor: {last_cursor}")
        return json_file_path, last_cursor

    except Exception as e:
        logger.error(f"[SCRAPE] Error: {e}")
        return None, None


def load_scraped_data(json_path: str) -> tuple[Optional[dict], list]:
    """Load scraped JSON file. Returns (brand_data, influencers_list)."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        brand_data = {
            "username": data.get("brand_username", ""),
            "captured_at": data.get("captured_at", "")
        }

        if isinstance(data.get("influencers"), list):
            influencers = data["influencers"]
        elif isinstance(data.get("data"), list):
            influencers = data["data"]
        else:
            influencers = data.get("influencers", [])

        logger.info(f"[LOAD] Loaded {len(influencers)} influencer entries from {json_path}")
        return brand_data, influencers

    except Exception as e:
        logger.error(f"[LOAD] Failed to load {json_path}: {e}")
        return None, []


def check_influencer_exists(username: str) -> Optional[dict]:
    """Check if influencer exists in DB."""
    try:
        response = requests.get(
            f"{BASE_URL}/free-influencers/",
            params={"username": username, "platform": "instagram"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("count", 0) > 0:
                return data["data"][0]
        return None
    except Exception as e:
        logger.error(f"[CHECK] Error for @{username}: {e}")
        return None


def create_influencer(data: dict) -> tuple[Optional[dict], bool]:
    """Save influencer to DB via POST. Returns (influencer_data, is_new)."""
    try:
        response = requests.post(
            f"{BASE_URL}/free-influencers/",
            json=data,
            timeout=10
        )
        if response.status_code == 201:
            logger.info(f"[CREATE] @{data.get('username')} saved to DB")
            return response.json(), True
        elif response.status_code in (400, 409) and "Conflict" in response.text:
            return {"id": data.get("id"), "username": data.get("username")}, False
        else:
            logger.error(f"[CREATE] Failed for @{data.get('username')}: HTTP {response.status_code}")
            return None, False
    except Exception as e:
        logger.error(f"[CREATE] Error for @{data.get('username')}: {e}")
        return None, False


def fetch_profile_from_rapidapi(username: str, retries: int = 2) -> Optional[dict]:
    """Fetch Instagram profile from RapidAPI."""
    import time
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

    for attempt in range(retries + 1):
        try:
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
                    return profile
            else:
                logger.warning(f"[RAPIDAPI] HTTP {response.status_code} for @{username}")
        except Exception as e:
            logger.warning(f"[RAPIDAPI] Error for @{username}: {e}")

        if attempt < retries:
            sleep_time = 2 ** attempt
            time.sleep(sleep_time)

    logger.error(f"[RAPIDAPI] Failed after {retries + 1} attempts for @{username}")
    return None


def build_influencer_data(profile: dict, json_data: dict) -> dict:
    """Build influencer data object for API."""
    import re
    import regex

    bio = profile.get("biography", "") or ""
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
            return data.get("count", 0) > 0
        return False
    except Exception as e:
        logger.error(f"[CHECK_COLLAB] Error: {e}")
        return False


def create_collaboration(data: dict) -> tuple[Optional[dict], bool]:
    """Create collaboration via POST API."""
    try:
        response = requests.post(
            f"{BASE_URL}/brand-collaborations/",
            json=data,
            timeout=10
        )
        if response.status_code == 201:
            logger.info(f"[COLLAB] Created: brand={data['brand_id']}, infl={data['influencer_id']}")
            return response.json(), True
        else:
            logger.error(f"[COLLAB] Failed: HTTP {response.status_code}")
            return None, False
    except Exception as e:
        logger.error(f"[COLLAB] Error: {e}")
        return None, False


def normalize_brand_id(raw_brand_id: str) -> str:
    """Normalize brand_id."""
    BRAND_ID_MAP = {
        "dot & key": "dot_and_key",
        "tira beauty": "tira_beauty",
    }
    return BRAND_ID_MAP.get(raw_brand_id, raw_brand_id)


def import_influencers(influencers: list, max_api_calls: int) -> dict:
    """Import influencers to DB. Returns stats."""
    stats = {
        "total": len(influencers),
        "existing": 0,
        "new": 0,
        "errors": 0,
        "api_calls_made": 0,
        "skipped": 0
    }

    for i, infl in enumerate(influencers):
        username = infl.get("username", "")
        if not username:
            continue

        logger.info(f"[IMPORT] [{i+1}/{len(influencers)}] Processing @{username}")

        existing = check_influencer_exists(username)
        if existing:
            stats["existing"] += 1
            stats["skipped"] += 1
            logger.info(f"[IMPORT] @{username} already exists, skipping")
            continue

        if stats["api_calls_made"] >= max_api_calls:
            logger.warning(f"[IMPORT] Max API calls reached ({max_api_calls}), skipping @{username}")
            stats["skipped"] += 1
            continue

        profile = fetch_profile_from_rapidapi(username, retries=2)
        if not profile:
            stats["errors"] += 1
            logger.error(f"[IMPORT] Failed to fetch profile for @{username}")
            continue

        stats["api_calls_made"] += 1

        influencer_data = build_influencer_data(profile, infl)
        if not influencer_data.get("id"):
            stats["errors"] += 1
            logger.error(f"[IMPORT] No ID in profile for @{username}")
            continue

        saved, is_new = create_influencer(influencer_data)
        if saved:
            stats["new"] += 1 if is_new else 0
            stats["existing"] += 1 if not is_new else 0
        else:
            stats["errors"] += 1

        logger.info(f"[IMPORT] Stats: New={stats['new']}, Existing={stats['existing']}, "
                   f"Errors={stats['errors']}, API calls={stats['api_calls_made']}/{max_api_calls}")

    logger.info(f"[IMPORT] Complete - New: {stats['new']}, Existing: {stats['existing']}, "
                f"Errors: {stats['errors']}, Skipped: {stats['skipped']}")
    return stats


def create_collaborations(influencers: list, brand_id: str) -> dict:
    """Create brand collaborations. Returns stats."""
    stats = {
        "total": len(influencers),
        "created": 0,
        "skipped_existing": 0,
        "missing_influencer": 0,
        "errors": 0
    }

    for i, infl in enumerate(influencers):
        username = infl.get("username", "")
        if not username:
            continue

        logger.info(f"[COLLAB] [{i+1}/{len(influencers)}] Processing @{username}")

        influencer = check_influencer_exists(username)
        if not influencer:
            stats["missing_influencer"] += 1
            logger.warning(f"[COLLAB] @{username} not found in DB")
            continue

        influencer_id = influencer["id"]

        if check_collaboration_exists(brand_id, influencer_id):
            stats["skipped_existing"] += 1
            logger.info(f"[COLLAB] Already exists: brand={brand_id}, infl={username}")
            continue

        collab_data = {
            "brand_id": brand_id,
            "influencer_id": influencer_id,
            "likes": int(infl.get("likes", 0)),
            "comments": int(infl.get("comments", 0)),
            "captured_at": datetime.utcnow().isoformat(),
            "post_link": infl.get("post_link", "") or None
        }

        collab, success = create_collaboration(collab_data)
        if success:
            stats["created"] += 1
        else:
            stats["errors"] += 1

        logger.info(f"[COLLAB] Stats: Created={stats['created']}, Skipped={stats['skipped_existing']}, "
                    f"Missing={stats['missing_influencer']}, Errors={stats['errors']}")

    logger.info(f"[COLLAB] Complete - Created: {stats['created']}, Skipped: {stats['skipped_existing']}, "
                f"Missing: {stats['missing_influencer']}, Errors: {stats['errors']}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Brand pipeline: scrape, import influencers, create collaborations")
    parser.add_argument("--brand", required=True, help="Brand Instagram username (without @)")
    parser.add_argument("--max-posts", type=int, default=20000, help="Max posts to scrape (default: 20000)")
    parser.add_argument("--max-api-calls", type=int, default=2000, help="Max API calls for scraping (default: 2000)")
    parser.add_argument("--max-db-api", type=int, default=0, help="Max DB API calls for import (0=unlimited)")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting Brand Pipeline")
    logger.info(f"Brand: @{args.brand}")
    logger.info(f"Max posts: {args.max_posts}")
    logger.info(f"Max API calls: {args.max_api_calls}")
    logger.info(f"Max DB API calls: {'unlimited' if args.max_db_api == 0 else args.max_db_api}")
    logger.info("=" * 60)

    json_file_path = None

    try:
        json_file_path, last_cursor = scrape_brand(
            args.brand, args.max_posts, args.max_api_calls
        )

        if not json_file_path:
            logger.error("[PIPELINE] Scraping failed, exiting")
            sys.exit(1)

        brand_data, influencers = load_scraped_data(json_file_path)
        if not influencers:
            logger.warning("[PIPELINE] No influencers found in scraped data")
            sys.exit(0)

        logger.info(f"[PIPELINE] Processing {len(influencers)} influencers")

        import_stats = import_influencers(
            influencers,
            args.max_db_api if args.max_db_api > 0 else float('inf')
        )

        brand_id = normalize_brand_id(brand_data.get("username", ""))
        collab_stats = create_collaborations(influencers, brand_id)

        output = {
            "completed_at": datetime.utcnow().isoformat(),
            "brand": args.brand,
            "brand_id": brand_id,
            "scraped_file": json_file_path,
            "last_cursor": last_cursor,
            "import_stats": import_stats,
            "collab_stats": collab_stats,
            "total_influencers": len(influencers)
        }

        os.makedirs("run-results", exist_ok=True)
        output_file = f"run-results/brand_pipeline_{args.brand}_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info("=" * 60)
        logger.info("Pipeline Complete")
        logger.info(f"Scraped: {len(influencers)} influencers")
        logger.info(f"Imported: {import_stats['new']} new, {import_stats['existing']} existing, "
                    f"{import_stats['errors']} errors")
        logger.info(f"Collaborations: {collab_stats['created']} created, "
                    f"{collab_stats['skipped_existing']} skipped, {collab_stats['missing_influencer']} missing")
        logger.info(f"Results saved to: {output_file}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("[PIPELINE] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[PIPELINE] Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
