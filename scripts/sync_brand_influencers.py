#!/usr/bin/env python3
"""
Sync brand influencers: scrape posts, extract influencers, upload avatars to Azure,
save to DB, and create brand collaborations.

Usage:
    python sync_brand_influencers.py --brand "mamaearth" --max-posts 10000 --max-api-calls 500
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional

import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "instagram120.p.rapidapi.com"
POSTS_API_URL = "https://instagram120.p.rapidapi.com/api/instagram/posts"
PROFILE_API_URL = "https://instagram120.p.rapidapi.com/api/instagram/profile"

AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
PROFILE_AVATARS_CONTAINER = "images"


def get_azure_storage():
    """Initialize Azure storage client."""
    if AZURE_STORAGE_CONNECTION_STRING:
        return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    elif AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY:
        account_url = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
        return BlobServiceClient(account_url=account_url, credential=AZURE_STORAGE_ACCOUNT_KEY)
    else:
        logger.error("Azure Storage not configured")
        return None


def fetch_posts(brand: str, max_posts: int, max_api_calls: int) -> tuple[list, Optional[str]]:
    """Fetch brand posts from RapidAPI."""
    all_posts = []
    max_id = ""
    api_call_count = 0
    consecutive_errors = 0
    max_consecutive_errors = 5

    while len(all_posts) < max_posts and api_call_count < max_api_calls:
        if api_call_count > 0 and (not max_id or max_id.strip() == ""):
            logger.info("No more pagination, stopping")
            break

        if consecutive_errors >= max_consecutive_errors:
            logger.error(f"Too many consecutive errors ({consecutive_errors}), stopping")
            break

        logger.info(f"Fetching posts for @{brand} (call {api_call_count + 1}, collected: {len(all_posts)})")

        try:
            response = requests.post(
                POSTS_API_URL,
                json={"username": brand, "maxId": max_id or ""},
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": RAPIDAPI_HOST,
                    "Content-Type": "application/json"
                },
                timeout=30
            )

            if response.status_code == 429:
                logger.error(f"Rate limited (429), stopping")
                break
            elif response.status_code != 200:
                consecutive_errors += 1
                logger.warning(f"API error: HTTP {response.status_code}, retrying... (attempt {consecutive_errors}/{max_consecutive_errors})")
                time.sleep(2)
                continue

            data = response.json()
            posts = data.get("result", {}).get("edges", [])

            if not posts:
                logger.info(f"No posts in response, breaking")
                break

            consecutive_errors = 0
            all_posts.extend(posts)

            page_info = data.get("result", {}).get("page_info", {})
            has_next = page_info.get("has_next_page", False)
            max_id = page_info.get("end_cursor", "") if has_next else ""
            api_call_count += 1

            logger.info(f"Got {len(posts)} posts, total: {len(all_posts)}")

        except Exception as e:
            consecutive_errors += 1
            logger.warning(f"Error fetching posts: {e}, retrying... (attempt {consecutive_errors}/{max_consecutive_errors})")
            time.sleep(2)
            continue

    logger.info(f"Finished fetching: {len(all_posts)} posts, {api_call_count} API calls")
    return all_posts, max_id if max_id else None


def extract_influencers(posts: list, brand: str) -> list:
    """Extract unique influencers from brand posts."""
    influencer_map = {}
    brand_lower = brand.lower()

    for post in posts:
        node = post.get("node", {})
        coauthors = node.get("coauthor_producers", [])
        post_code = node.get("code", "")
        post_link = f"https://www.instagram.com/p/{post_code}/" if post_code else ""

        post_owner = node.get("owner", {})
        is_brand_post = post_owner.get("username", "").lower() == brand_lower

        if is_brand_post:
            for coauthor in coauthors:
                username = coauthor.get("username", "")
                user_id = coauthor.get("pk") or coauthor.get("id")

                if username.lower() == brand_lower or not user_id:
                    continue

                if username not in influencer_map:
                    influencer_map[username] = {
                        "username": username,
                        "user_id": str(user_id),
                        "full_name": coauthor.get("full_name", ""),
                        "likes": node.get("like_count", 0),
                        "comments": node.get("comment_count", 0),
                        "post_link": post_link,
                        "profile_pic_url": coauthor.get("profile_p_url", ""),
                    }

    return list(influencer_map.values())


def save_json(data: Any, filepath: str):
    """Save data to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {filepath}")


def load_json(filepath: str) -> Optional[Any]:
    """Load data from JSON file."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_profile(username: str, retries: int = 2) -> Optional[dict]:
    """Fetch Instagram profile from RapidAPI."""
    for attempt in range(retries + 1):
        try:
            response = requests.post(
                PROFILE_API_URL,
                json={"username": username},
                headers={
                    "X-RapidAPI-Key": RAPIDAPI_KEY,
                    "X-RapidAPI-Host": RAPIDAPI_HOST,
                    "Content-Type": "application/json"
                },
                timeout=30
            )

            if response.status_code == 200:
                profile = response.json().get("result", {})
                if profile:
                    return profile

            if attempt < retries:
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{retries} for @{username} after {wait_time}s")
                time.sleep(wait_time)

        except Exception as e:
            logger.warning(f"Error fetching profile for @{username}: {e}")
            if attempt < retries:
                time.sleep(2 ** attempt)

    logger.error(f"Failed to fetch profile for @{username} after {retries + 1} attempts")
    return None


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
    except Exception as e:
        logger.error(f"Error checking influencer @{username}: {e}")
    return None


def create_influencer(data: dict) -> Optional[dict]:
    """Create influencer in DB."""
    try:
        response = requests.post(
            f"{BASE_URL}/free-influencers/",
            json=data,
            timeout=10
        )
        if response.status_code == 201:
            logger.info(f"Created influencer: @{data.get('username')}")
            return response.json()
        elif response.status_code in (400, 409):
            logger.info(f"Influencer @{data.get('username')} already exists")
            return data
        else:
            logger.error(f"Failed to create @{data.get('username')}: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Error creating influencer @{data.get('username')}: {e}")
    return None


def check_collaboration_exists(brand_id: str, influencer_id: Optional[str]) -> bool:
    """Check if collaboration exists."""
    try:
        response = requests.get(
            f"{BASE_URL}/brand-collaborations",
            params={"brand_id": brand_id, "influencer_id": influencer_id},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("count", 0) > 0
    except Exception as e:
        logger.error(f"Error checking collaboration: {e}")
    return False


def create_collaboration(data: dict) -> Optional[dict]:
    """Create brand collaboration in DB."""
    try:
        response = requests.post(
            f"{BASE_URL}/brand-collaborations/",
            json=data,
            timeout=10
        )
        if response.status_code == 201:
            return response.json()
        else:
            logger.error(f"Failed to create collaboration: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Error creating collaboration: {e}")
    return None


def download_image(url: str) -> Optional[bytes]:
    """Download image from URL."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.content
    except Exception as e:
        logger.warning(f"Error downloading image from {url}: {e}")
    return None


def upload_to_azure(storage: BlobServiceClient, image_data: bytes, username: str) -> Optional[str]:
    """Upload avatar to Azure and return URL."""
    try:
        blob_name = f"profile-avatars/{username}.jpg"
        blob_client = storage.get_blob_client(container=PROFILE_AVATARS_CONTAINER, blob=blob_name)
        blob_client.upload_blob(image_data, overwrite=True, content_settings=ContentSettings(content_type="image/jpeg"))
        url = blob_client.url
        logger.info(f"Uploaded avatar for @{username}: {url}")
        return url
    except Exception as e:
        logger.error(f"Error uploading avatar for @{username}: {e}")
    return None


def build_influencer_data(profile: dict, scraped_data: dict, azure_url: Optional[str] = None) -> dict:
    """Build influencer data object for DB."""
    import re
    import regex

    bio = profile.get("biography", "") or ""
    try:
        bio = regex.sub(r"[\p{Extended_Pictographic}\p{Emoji_Presentation}\p{Symbol}]", "", bio, flags=regex.UNICODE)
        bio = re.sub(r"\s+", " ", bio).strip()
    except Exception:
        pass

    profile_pic_url = profile.get("profile_pic_url", "")
    profile_pic_url_hd = profile.get("profile_pic_url_hd", "")

    return {
        "id": str(profile.get("id")) if profile.get("id") else None,
        "platform": "instagram",
        "platform_user_id": str(profile.get("id")) if profile.get("id") else None,
        "username": profile.get("username", ""),
        "full_name": profile.get("full_name") or scraped_data.get("full_name", "") or scraped_data.get("username", ""),
        "bio": bio if bio else None,
        "is_private": profile.get("is_private", False),
        "followers": profile.get("edge_followed_by", {}).get("count", 0),
        "following": profile.get("edge_follow", {}).get("count", 0),
        "post_count": profile.get("edge_owner_to_timeline_media", {}).get("count", 0),
        "profile_image": {
            "url": azure_url or profile_pic_url,
            "hd": profile_pic_url_hd
        },
        "last_fetched_at": datetime.now(timezone.utc).isoformat()
    }


def process_brand(brand: str, max_posts: int, max_api_calls: int):
    """Main processing function."""
    logger.info("=" * 60)
    logger.info(f"Starting sync for @{brand}")
    logger.info("=" * 60)

    infl_file = f"{brand}_infl.json"
    posts_file = f"{brand}_posts.json"
    captured_at = datetime.now(timezone.utc).isoformat()

    influencers = load_json(infl_file)
    load_json(posts_file)

    if influencers is None:
        logger.info("No cached influencer data, fetching from RapidAPI...")
        posts, cursor = fetch_posts(brand, max_posts, max_api_calls)
        posts_data = {"posts": posts, "cursor": cursor, "captured_at": captured_at}
        save_json(posts_data, posts_file)

        influencers = extract_influencers(posts, brand)
        infl_data = {
            "brand_username": brand,
            "captured_at": captured_at,
            "influencers": influencers
        }
        save_json(infl_data, infl_file)
        logger.info(f"Extracted {len(influencers)} unique influencers")
    else:
        influencers = influencers.get("influencers", influencers)
        logger.info(f"Loaded {len(influencers)} influencers from cache")

    if not influencers:
        logger.warning("No influencers found")
        return

    storage = get_azure_storage()
    if not storage:
        logger.error("Azure Storage not available")
        return

    stats = {"total": len(influencers), "existing": 0, "new": 0, "collaborations": 0, "errors": 0}

    for i, infl in enumerate(influencers):
        username = infl.get("username", "")
        if not username:
            continue

        logger.info(f"[{i+1}/{len(influencers)}] Processing @{username}")

        existing = check_influencer_exists(username)

        if existing:
            stats["existing"] += 1
            logger.info(f"@{username} already exists, skipping")
        else:
            profile = fetch_profile(username)
            if not profile:
                stats["errors"] += 1
                logger.error(f"Failed to fetch profile for @{username}")
                continue

            azure_url = None
            profile_pic_url_hd = profile.get("profile_pic_url_hd", "")
            if profile_pic_url_hd:
                image_data = download_image(profile_pic_url_hd)
                if image_data:
                    azure_url = upload_to_azure(storage, image_data, username)

            infl_data = build_influencer_data(profile, infl, azure_url)

            if not infl_data.get("id"):
                stats["errors"] += 1
                logger.error(f"No ID in profile for @{username}")
                continue

            saved = create_influencer(infl_data)
            if saved:
                stats["new"] += 1
                existing = saved
            else:
                stats["errors"] += 1
                continue

        if not existing:
            stats["errors"] += 1
            continue

        influencer_id = existing.get("id")
        if check_collaboration_exists(brand, influencer_id):
            logger.info(f"Collaboration already exists for @{username}")
            continue

        collab_data = {
            "brand_id": brand,
            "influencer_id": influencer_id,
            "likes": int(infl.get("likes", 0)),
            "comments": int(infl.get("comments", 0)),
            "captured_at": infl.get("captured_at") or captured_at,
            "post_link": infl.get("post_link", "") or None
        }

        if create_collaboration(collab_data):
            stats["collaborations"] += 1
        else:
            stats["errors"] += 1

    logger.info("=" * 60)
    logger.info(f"Sync complete for @{brand}")
    logger.info(f"Total: {stats['total']}, New: {stats['new']}, Existing: {stats['existing']}")
    logger.info(f"Collaborations: {stats['collaborations']}, Errors: {stats['errors']}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Sync brand influencers to DB")
    parser.add_argument("--brand", required=True, help="Brand Instagram username (without @)")
    parser.add_argument("--max-posts", type=int, default=10000, help="Max posts to fetch")
    parser.add_argument("--max-api-calls", type=int, default=500, help="Max API calls")
    args = parser.parse_args()

    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY not set")
        sys.exit(1)

    process_brand(args.brand, args.max_posts, args.max_api_calls)


if __name__ == "__main__":
    main()
