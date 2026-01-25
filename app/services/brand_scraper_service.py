"""Brand scraper service for fetching Instagram posts and extracting influencer data."""
import asyncio
import logging
import os
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import aiohttp
from difflib import SequenceMatcher

from app.core.config import settings

logger = logging.getLogger(__name__)

RAPIDAPI_URL = "https://instagram120.p.rapidapi.com/api/instagram/posts"
RAPIDAPI_HOST = "instagram120.p.rapidapi.com"
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_MS = 1000  # 1 second
MAX_RETRY_DELAY_MS = 10000  # 10 seconds


class InstagramPost:
    """Instagram post data structure."""
    
    def __init__(self, data: Dict[str, Any]):
        self.node = data.get("node", {})
        self.code = self.node.get("code")
        self.pk = self.node.get("pk")
        self.user = self.node.get("user", {})
        self.owner = self.node.get("owner")
        self.coauthor_producers = self.node.get("coauthor_producers", [])
        self.like_count = self.node.get("like_count")
        self.comment_count = self.node.get("comment_count")
        self.view_count = self.node.get("view_count")
        self.play_count = self.node.get("play_count")
        self.caption = self.node.get("caption", {})


class BrandData:
    """Brand data structure."""
    
    def __init__(
        self,
        username: str,
        full_name: Optional[str] = None,
        user_id: Optional[str] = None,
        is_verified: Optional[bool] = None,
    ):
        self.username = username
        self.full_name = full_name
        self.user_id = user_id
        self.is_verified = is_verified


class InfluencerData:
    """Influencer data structure."""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        full_name: Optional[str] = None,
        is_verified: Optional[bool] = None,
        post_code: Optional[str] = None,
        post_link: Optional[str] = None,
        profile_pic_url: Optional[str] = None,
        follower_count: Optional[int] = None,
        likes: Optional[int] = None,
        comments: Optional[int] = None,
        views: Optional[int] = None,
        shares: Optional[int] = None,
    ):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.is_verified = is_verified
        self.post_code = post_code
        self.post_link = post_link
        self.profile_pic_url = profile_pic_url
        self.follower_count = follower_count
        self.likes = likes
        self.comments = comments
        self.views = views
        self.shares = shares


async def make_api_call_with_retry(
    session: aiohttp.ClientSession,
    username: str,
    max_id: str,
    call_number: int,
    retry_count: int = 0,
) -> aiohttp.ClientResponse:
    """
    Makes an API call with retry logic and exponential backoff.
    
    Args:
        session: aiohttp client session
        username: Instagram username
        max_id: Pagination cursor
        call_number: Call number for logging
        retry_count: Current retry attempt
        
    Returns:
        aiohttp.ClientResponse
    """
    request_body = {
        "username": username,
        "maxId": max_id or "",
    }
    
    try:
        # Don't use context manager for response to allow reading outside
        response = await session.post(
            RAPIDAPI_URL,
            json=request_body,
            headers={
                "Content-Type": "application/json",
                "x-rapidapi-host": RAPIDAPI_HOST,
                "x-rapidapi-key": settings.RAPIDAPI_KEY,
            },
        )
        
        # If response is successful, return it
        if response.status == 200:
            return response
        
        # Determine if we should retry based on status code
        status = response.status
        should_retry = (
            status >= 500  # Server errors (5xx)
            or status == 429  # Rate limit
            or status == 408  # Request timeout
            or status == 503  # Service unavailable
            or status == 504  # Gateway timeout
        )
        
        # Don't retry on client errors (4xx) except rate limit and timeout
        if not should_retry and retry_count < MAX_RETRIES:
            # For 4xx errors (except 429, 408), don't retry
            if 400 <= status < 500:
                return response  # Return the error response
        
        # If we should retry and haven't exceeded max retries
        if should_retry and retry_count < MAX_RETRIES:
            # Close the current response before retrying
            response.close()
            
            # Calculate exponential backoff delay
            delay = min(
                INITIAL_RETRY_DELAY_MS * (2 ** retry_count),
                MAX_RETRY_DELAY_MS
            )
            
            logger.warning(
                f"[API Call {call_number}] Request failed with status {status}. "
                f"Retrying in {delay}ms... (Attempt {retry_count + 1}/{MAX_RETRIES})"
            )
            
            await asyncio.sleep(delay / 1000.0)
            
            # Retry the request
            return await make_api_call_with_retry(
                session, username, max_id, call_number, retry_count + 1
            )
        
        # If we've exhausted retries or shouldn't retry, return the response
        return response
            
    except Exception as error:
        # Network errors or other exceptions - retry if we haven't exceeded retries
        if retry_count < MAX_RETRIES:
            delay = min(
                INITIAL_RETRY_DELAY_MS * (2 ** retry_count),
                MAX_RETRY_DELAY_MS
            )
            
            logger.warning(
                f"[API Call {call_number}] Network/request error: {str(error)}. "
                f"Retrying in {delay}ms... (Attempt {retry_count + 1}/{MAX_RETRIES})"
            )
            
            await asyncio.sleep(delay / 1000.0)
            
            # Retry the request
            return await make_api_call_with_retry(
                session, username, max_id, call_number, retry_count + 1
            )
        
        # If we've exhausted retries, raise the error
        raise


async def fetch_brand_posts(
    username: str,
    max_posts: int,
    max_api_calls: int = 20,
    start_max_id: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Fetch brand posts from Instagram API.
    
    Args:
        username: Brand Instagram username
        max_posts: Maximum number of posts to fetch
        max_api_calls: Maximum number of API calls
        start_max_id: Last cursor/end_cursor from previous scrape to resume
        
    Returns:
        Tuple of (posts list, last_cursor)
    """
    all_posts: List[Dict[str, Any]] = []
    max_id = start_max_id or ""
    api_call_count = 0
    
    if start_max_id:
        logger.info(f"[fetchBrandPosts] Starting from cursor: {start_max_id}")
    
    async with aiohttp.ClientSession() as session:
        while len(all_posts) < max_posts and api_call_count < max_api_calls:
            try:
                # If maxId is null/empty after the first call, stop making API calls
                if api_call_count > 0 and (not max_id or max_id.strip() == ""):
                    logger.info(
                        f"[API Call {api_call_count + 1}] maxId is null or empty. Stopping API calls."
                    )
                    break
                
                logger.info(
                    f"[API Call {api_call_count + 1}] Fetching posts for @{username}, "
                    f"maxId: {max_id or 'empty'}, posts collected: {len(all_posts)}"
                )
                
                # Make API call with retry logic
                response = await make_api_call_with_retry(
                    session, username, max_id, api_call_count + 1
                )
                
                try:
                    # Log response headers for debugging
                    rate_limit_remaining = response.headers.get("x-ratelimit-requests-remaining")
                    rate_limit_reset = response.headers.get("x-ratelimit-requests-reset")
                    
                    if rate_limit_remaining:
                        logger.info(
                            f"[API Call {api_call_count + 1}] Rate limit remaining: {rate_limit_remaining}"
                        )
                    
                    if response.status != 200:
                        # Try to get error details from response body
                        error_details = ""
                        try:
                            error_body = await response.text()
                            error_details = error_body
                            logger.error(
                                f"[API Call {api_call_count + 1}] Error response body (after retries): {error_body}"
                            )
                        except Exception:
                            # Ignore if we can't read the body
                            pass
                        
                        error_message = (
                            f"API request failed after {MAX_RETRIES} retries: "
                            f"{response.status} {response.reason}"
                            f"{f' - {error_details}' if error_details else ''}"
                        )
                        logger.error(
                            f"[API Call {api_call_count + 1}] Request details: "
                            f"url={RAPIDAPI_URL}, username={username}, "
                            f"maxId={max_id or 'empty'}, apiCallCount={api_call_count + 1}, "
                            f"postsCollected={len(all_posts)}, status={response.status}, "
                            f"statusText={response.reason}, rateLimitRemaining={rate_limit_remaining}, "
                            f"rateLimitReset={rate_limit_reset}"
                        )
                        
                        # If it's a rate limit error (429) after retries, wait longer before breaking
                        if response.status == 429:
                            logger.warning(
                                f"[API Call {api_call_count + 1}] Rate limit hit after retries. "
                                "Waiting 5 seconds before breaking..."
                            )
                            await asyncio.sleep(5)
                            break
                        
                        # For 500 errors after retries, log more details and break
                        if response.status >= 500:
                            logger.error(
                                f"[API Call {api_call_count + 1}] Server error ({response.status}) after retries. "
                                "This might be due to:"
                            )
                            logger.error(f"  - Invalid maxId/cursor: {max_id or 'empty'}")
                            logger.error("  - API quota exceeded")
                            logger.error("  - Instagram API issues")
                            logger.error("  - Invalid username or pagination state")
                            
                            # If we have some posts, return what we have instead of breaking completely
                            if len(all_posts) > 0:
                                logger.warning(
                                    f"[API Call {api_call_count + 1}] Returning {len(all_posts)} posts collected so far"
                                )
                                break
                        
                        # For 4xx errors (client errors), break without retrying further
                        if 400 <= response.status < 500:
                            logger.error(
                                f"[API Call {api_call_count + 1}] Client error ({response.status}) after retries. Breaking."
                            )
                            break
                        
                        raise Exception(error_message)
                    
                    data = await response.json()
                finally:
                    # Ensure response is closed
                    response.close()
                
                if not data.get("result") or not data["result"].get("edges"):
                    logger.info(
                        f"[API Call {api_call_count + 1}] No result or edges in response. Breaking."
                    )
                    break
                
                edges = data["result"]["edges"]
                logger.info(
                    f"[API Call {api_call_count + 1}] Successfully fetched {len(edges)} posts"
                )
                
                all_posts.extend(edges)
                
                page_info = data["result"].get("page_info", {})
                if not page_info.get("has_next_page"):
                    logger.info(
                        f"[API Call {api_call_count + 1}] No more pages available. Breaking."
                    )
                    break
                
                # Check if end_cursor exists and is not null/empty
                end_cursor = page_info.get("end_cursor")
                if not end_cursor or end_cursor is None or end_cursor.strip() == "":
                    logger.info(
                        f"[API Call {api_call_count + 1}] end_cursor is null or empty. Stopping API calls."
                    )
                    max_id = ""  # Set to empty to prevent next iteration
                    break
                
                logger.info(
                    f"[API Call {api_call_count + 1}] end_cursor: {end_cursor} "
                    "(use this to resume from this point)"
                )
                max_id = end_cursor
                api_call_count += 1
                
                # Add a small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as error:
                logger.error(f"[API Call {api_call_count + 1}] Error fetching posts: {error}")
                logger.error(
                    f"[API Call {api_call_count + 1}] Error stack: "
                    f"{str(error.__class__.__name__)}: {str(error)}"
                )
                
                # If we have some posts, return what we have
                if len(all_posts) > 0:
                    logger.warning(
                        f"[API Call {api_call_count + 1}] Returning {len(all_posts)} posts "
                        "collected before error"
                    )
                    break
                
                # If no posts collected and it's not the first call, break
                if api_call_count > 0:
                    break
                
                # Re-raise error if it's the first call and we have no posts
                raise
    
    final_posts = all_posts[:max_posts]
    last_cursor = max_id if (max_id and max_id.strip() != "") else None
    
    logger.info(
        f"[fetchBrandPosts Summary] Username: @{username}, Requested: {max_posts}, "
        f"Collected: {len(final_posts)}, API Calls: {api_call_count}"
    )
    if last_cursor:
        logger.info(
            f"[fetchBrandPosts Summary] Last end_cursor: {last_cursor} "
            "(use this to resume scraping)"
        )
    
    return final_posts, last_cursor


def extract_brand_data(posts: List[Dict[str, Any]], brand_username: str) -> BrandData:
    """
    Extract brand data from posts.
    
    Args:
        posts: List of Instagram post data
        brand_username: Brand username
        
    Returns:
        BrandData object
    """
    # Find brand from first post - check user or owner field
    if not posts:
        return BrandData(username=brand_username)
    
    first_post = posts[0]
    node = first_post.get("node", {})
    user = node.get("user", {})
    owner = node.get("owner")
    
    # Determine which one is the brand (the one matching the username)
    if user.get("username", "").lower() == brand_username.lower():
        return BrandData(
            username=user.get("username", brand_username),
            full_name=user.get("full_name"),
            user_id=user.get("pk") or user.get("id"),
            is_verified=user.get("is_verified"),
        )
    
    if owner and owner.get("username", "").lower() == brand_username.lower():
        return BrandData(
            username=owner.get("username", brand_username),
            user_id=owner.get("pk"),
        )
    
    return BrandData(username=brand_username)


def normalize_username(username: str) -> str:
    """
    Normalizes a username by removing common suffixes and domain extensions.
    
    Examples: "mamaearth.in" -> "mamaearth", "mamaearth_global" -> "mamaearth"
    
    Args:
        username: Username to normalize
        
    Returns:
        Normalized username
    """
    normalized = username.lower()
    
    # Remove common domain extensions
    import re
    normalized = re.sub(r"\.(in|com|co|io|net|org|uk|us|au|ca)$", "", normalized, flags=re.IGNORECASE)
    
    # Remove common account type suffixes
    suffixes = [
        "_global", "_official", "_india", "_world", "_international",
        "_official_", "_verified", "_brand", "_store", "_shop", "_officialpage",
        "official_", "global_", "india_", "world_", "brand_", "officialpage_",
        "_page", "_account", "_insta", "_ig"
    ]
    
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
        if normalized.startswith(suffix):
            normalized = normalized[len(suffix):]
    
    # Remove trailing/leading underscores and hyphens
    normalized = re.sub(r"^[_-]+|[_-]+$", "", normalized)
    
    return normalized


def is_similar_username(
    username1: str, username2: str, similarity_threshold: float = 0.85
) -> bool:
    """
    Checks if two usernames are similar (likely the same brand with different accounts).
    
    Uses string similarity and normalization to detect variations like:
    - mamaearth.in vs mamaearth_global
    - mynykaa vs mynykaa_official
    
    Args:
        username1: First username
        username2: Second username
        similarity_threshold: Similarity threshold (0-1)
        
    Returns:
        True if usernames are similar
    """
    normalized1 = normalize_username(username1)
    normalized2 = normalize_username(username2)
    
    # If normalized usernames are identical, they're definitely similar
    if normalized1 == normalized2 and len(normalized1) > 0:
        return True
    
    # Calculate similarity score using SequenceMatcher
    similarity = SequenceMatcher(None, normalized1, normalized2).ratio()
    
    # Also check if one normalized username contains the other (for partial matches)
    contains_match = (
        len(normalized1) >= 5
        and len(normalized2) >= 5
        and (normalized1 in normalized2 or normalized2 in normalized1)
    )
    
    return similarity >= similarity_threshold or contains_match


def extract_influencer_data(
    posts: List[Dict[str, Any]],
    brand_username: str,
    exclude_usernames: Optional[List[str]] = None,
) -> List[InfluencerData]:
    """
    Extract influencer data from brand posts.
    
    Args:
        posts: List of Instagram post data
        brand_username: Brand username to filter out
        exclude_usernames: List of usernames to exclude
        
    Returns:
        List of InfluencerData objects
    """
    if exclude_usernames is None:
        exclude_usernames = []
    
    # Use both user_id and username as keys to prevent duplicates
    influencer_map_by_id: Dict[str, InfluencerData] = {}
    influencer_map_by_username: Dict[str, InfluencerData] = {}
    exclude_set = {u.lower().strip() for u in exclude_usernames}
    
    # Helper function to check if influencer should be added
    def should_add_influencer(username: str, user_id: str) -> bool:
        username_lower = username.lower().strip()
        
        # Skip if in exclude list
        if username_lower in exclude_set:
            logger.info(f"[extractInfluencerData] Skipping excluded username: @{username}")
            return False
        
        # Skip if already exists by ID or username
        if user_id in influencer_map_by_id or username_lower in influencer_map_by_username:
            return False
        
        return True
    
    # Helper function to add influencer
    def add_influencer(influencer_data: InfluencerData):
        username_lower = influencer_data.username.lower().strip()
        influencer_map_by_id[influencer_data.user_id] = influencer_data
        influencer_map_by_username[username_lower] = influencer_data
    
    for post in posts:
        node = post.get("node", {})
        post_user = node.get("user", {})
        post_owner = node.get("owner")
        coauthors = node.get("coauthor_producers", [])
        
        # Determine if the post user/owner is the brand
        is_brand_post = (
            post_user.get("username", "").lower() == brand_username.lower()
            or (post_owner and post_owner.get("username", "").lower() == brand_username.lower())
        )
        
        if is_brand_post:
            # Brand posted, collaborators are in coauthor_producers
            post_code = node.get("code")
            post_link = f"https://www.instagram.com/p/{post_code}/" if post_code else None
            
            for coauthor in coauthors:
                coauthor_username = coauthor.get("username", "")
                # Skip if coauthor is the brand itself or similar username
                if (
                    coauthor_username.lower() == brand_username.lower()
                    or is_similar_username(coauthor_username, brand_username)
                ):
                    logger.info(
                        f"[extractInfluencerData] Skipping similar username: "
                        f"@{coauthor_username} (brand: @{brand_username})"
                    )
                    continue
                
                influencer_id = coauthor.get("pk") or coauthor.get("id")
                if should_add_influencer(coauthor_username, influencer_id):
                    add_influencer(
                        InfluencerData(
                            user_id=influencer_id,
                            username=coauthor_username,
                            full_name=coauthor.get("full_name"),
                            is_verified=coauthor.get("is_verified"),
                            post_code=post_code,
                            post_link=post_link,
                            profile_pic_url=coauthor.get("profile_pic_url"),
                            follower_count=coauthor.get("follower_count"),
                            likes=node.get("like_count"),
                            comments=node.get("comment_count"),
                            views=node.get("view_count") or node.get("play_count"),
                        )
                    )
        else:
            # Influencer posted, brand might be in coauthors or the influencer is the user
            # If brand is in coauthors, then user is the influencer
            brand_in_coauthors = any(
                c.get("username", "").lower() == brand_username.lower()
                or is_similar_username(c.get("username", ""), brand_username)
                for c in coauthors
            )
            
            if brand_in_coauthors:
                # The post user is the influencer (make sure it's not the brand)
                influencer_id = post_user.get("pk") or post_user.get("id")
                influencer_username = post_user.get("username", "").lower()
                post_code = node.get("code")
                post_link = f"https://www.instagram.com/p/{post_code}/" if post_code else None
                
                # Only add if it's not the brand and not a similar username
                if (
                    influencer_username != brand_username.lower()
                    and not is_similar_username(post_user.get("username", ""), brand_username)
                    and should_add_influencer(post_user.get("username", ""), influencer_id)
                ):
                    add_influencer(
                        InfluencerData(
                            user_id=influencer_id,
                            username=post_user.get("username", ""),
                            full_name=post_user.get("full_name"),
                            is_verified=post_user.get("is_verified"),
                            post_code=post_code,
                            post_link=post_link,
                            profile_pic_url=post_user.get("profile_pic_url"),
                            follower_count=None,  # Not available in user object from posts API
                            likes=node.get("like_count"),
                            comments=node.get("comment_count"),
                            views=node.get("view_count") or node.get("play_count"),
                        )
                    )
                
                # Also extract other coauthors (not the brand) as influencers
                # This handles cases where multiple influencers collaborated with the brand
                for coauthor in coauthors:
                    coauthor_username = coauthor.get("username", "")
                    # Skip if coauthor is the brand itself or similar username
                    if (
                        coauthor_username.lower() == brand_username.lower()
                        or is_similar_username(coauthor_username, brand_username)
                    ):
                        continue
                    
                    coauthor_id = coauthor.get("pk") or coauthor.get("id")
                    if should_add_influencer(coauthor_username, coauthor_id):
                        add_influencer(
                            InfluencerData(
                                user_id=coauthor_id,
                                username=coauthor_username,
                                full_name=coauthor.get("full_name"),
                                is_verified=coauthor.get("is_verified"),
                                post_code=post_code,
                                post_link=post_link,
                                profile_pic_url=coauthor.get("profile_pic_url"),
                                follower_count=coauthor.get("follower_count"),
                                likes=node.get("like_count"),
                                comments=node.get("comment_count"),
                                views=node.get("view_count") or node.get("play_count"),
                            )
                        )
    
    # Get unique influencers (using Map by ID to get final list)
    influencers = list(influencer_map_by_id.values())
    
    # Final filter to remove any excluded usernames (double-check)
    filtered_influencers = [
        inf
        for inf in influencers
        if inf.username.lower().strip() not in exclude_set
    ]
    
    return filtered_influencers


async def generate_excel_file(
    brand_data: BrandData,
    influencer_data: List[InfluencerData],
    output_folder: str = "scraped_data",
) -> str:
    """
    Generate Excel file with brand and influencer data.
    
    Args:
        brand_data: Brand data
        influencer_data: List of influencer data
        output_folder: Output folder path
        
    Returns:
        File path of generated Excel file
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        raise ImportError(
            "openpyxl is required for Excel generation. Install it with: pip install openpyxl"
        )
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create workbook
    workbook = Workbook()
    
    # Create Brands sheet
    brands_sheet = workbook.active
    brands_sheet.title = "Brands"
    brands_sheet.append(["Instagram Handle", "Full Name"])
    
    # Style header row
    for cell in brands_sheet[1]:
        cell.font = Font(bold=True)
    
    brands_sheet.append([
        f"https://instagram.com/{brand_data.username}",
        brand_data.full_name or "",
    ])
    
    # Set column widths
    brands_sheet.column_dimensions["A"].width = 50
    brands_sheet.column_dimensions["B"].width = 30
    
    # Create Influencers sheet
    influencers_sheet = workbook.create_sheet("Influencers")
    influencers_sheet.append(["Instagram Handle", "Full Name", "Post Link", "Likes", "Comments"])
    
    # Style header row
    for cell in influencers_sheet[1]:
        cell.font = Font(bold=True)
    
    for influencer in influencer_data:
        influencers_sheet.append([
            f"https://instagram.com/{influencer.username}",
            influencer.full_name or "",
            influencer.post_link or "",
            influencer.likes or 0,
            influencer.comments or 0,
        ])
    
    # Set column widths
    influencers_sheet.column_dimensions["A"].width = 50
    influencers_sheet.column_dimensions["B"].width = 30
    influencers_sheet.column_dimensions["C"].width = 50
    influencers_sheet.column_dimensions["D"].width = 15
    influencers_sheet.column_dimensions["E"].width = 15
    
    # Generate filename with timestamp
    timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")[:19]
    filename = f"brand_scrape_{brand_data.username}_{timestamp}.xlsx"
    filepath = os.path.join(output_folder, filename)
    
    # Write file
    workbook.save(filepath)
    
    return filepath
