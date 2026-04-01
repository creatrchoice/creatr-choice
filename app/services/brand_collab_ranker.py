"""Brand collab ranker service for ranking influencers by brand collaborations."""
import json
import hashlib
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import timedelta

import redis
from app.db.redis import redis_client
from app.db.cosmos_db import CosmosDBClient
from app.repositories.brand_repository import BrandRepository
from app.repositories.brand_collaboration_repository import BrandCollaborationRepository
from app.config import scoring_config

logger = logging.getLogger(__name__)


class BrandCollabRanker:
    """Service to rank and search influencers by brand collaborations."""

    def __init__(self):
        self.brand_repo = BrandRepository()
        self.collab_repo = BrandCollaborationRepository()
        self.cosmos_client = CosmosDBClient()

    async def _get_brands_container(self):
        """Get brands container."""
        from app.core.config import settings
        return await self.cosmos_client.get_async_container_client(settings.AZURE_COSMOS_BRANDS_CONTAINER)

    async def _get_collabs_container(self):
        """Get brand_collaborations container."""
        from app.core.config import settings
        return await self.cosmos_client.get_async_container_client(settings.AZURE_COSMOS_BRAND_COLLABORATIONS_CONTAINER)

    async def refresh_category_rankings(self) -> Dict[str, Any]:
        """
        Refresh all category rankings in Redis.
        
        This is an admin-triggered batch job that:
        1. Fetches all brands and their categories
        2. Fetches all brand_collaborations
        3. For each category, scores all influencers who worked with brands in that category
        4. Stores sorted list in Redis sorted sets
        """
        start_time = time.time()
        logger.info("Starting category rankings refresh")
        
        # Step 1: Fetch all brands and their categories
        brands_container = await self._get_brands_container()
        brand_categories: Dict[str, List[str]] = {}  # brand_id -> categories
        
        query = "SELECT c.id, c.categories FROM c"
        async for brand in brands_container.query_items(query=query):
            brand_id = brand.get("id")
            categories = brand.get("categories") or []
            if brand_id and categories:
                brand_categories[brand_id] = categories
        
        logger.info(f"Found {len(brand_categories)} brands with categories")
        
        # Step 2: Build category -> brands mapping
        category_brands: Dict[str, List[str]] = {}  # category -> list of brand_ids
        for brand_id, cats in brand_categories.items():
            for cat in cats:
                if cat not in category_brands:
                    category_brands[cat] = []
                category_brands[cat].append(brand_id)
        
        # Step 3: Fetch all brand_collaborations and group by influencer
        collabs_container = await self._get_collabs_container()
        
        # influencer_collabs: influencer_id -> [{brand_id, categories, ...}]
        influencer_collabs: Dict[str, List[Dict]] = {}
        
        query = """
            SELECT c.brand_id, c.influencer_id, c.platform, c.followers, c.post_count, 
                   c.username, c.full_name, c.profile_image, c.bio
            FROM c
        """
        async for collab in collabs_container.query_items(query=query):
            influencer_id = collab.get("influencer_id")
            brand_id = collab.get("brand_id")
            
            if not influencer_id or not brand_id:
                continue
            
            brand_cats = brand_categories.get(brand_id, [])
            
            # Handle profile_image extraction
            profile_img = collab.get("profile_image")
            profile_img_url = None
            if profile_img and isinstance(profile_img, dict):
                profile_img_url = profile_img.get("url")
            
            if influencer_id not in influencer_collabs:
                influencer_collabs[influencer_id] = []
            
            influencer_collabs[influencer_id].append({
                "brand_id": brand_id,
                "categories": brand_cats,
                "followers": collab.get("followers", 0) or 0,
                "post_count": collab.get("post_count", 0) or 0,
                "platform": collab.get("platform", "instagram"),
                "username": collab.get("username", ""),
                "full_name": collab.get("full_name", ""),
                "profile_image_url": profile_img_url,
                "bio": collab.get("bio", ""),
            })
        
        logger.info(f"Found {len(influencer_collabs)} unique influencers")
        
        # Step 4: Score influencers for each category
        scoring = scoring_config.INFLUENCER_SCORING
        follower_w = scoring["follower_weight"]
        post_ratio_w = scoring["post_ratio_weight"]
        collab_count_w = scoring["collab_count_weight"]
        
        # Find max followers for normalization
        max_followers = 1
        for collabs in influencer_collabs.values():
            for c in collabs:
                if c["followers"] > max_followers:
                    max_followers = c["followers"]
        
        # category_influencers: category -> [(infl_id, infl_data, score), ...]
        category_influencers: Dict[str, List[Tuple[str, Dict, float]]] = {}
        
        for category, brand_ids in category_brands.items():
            category_set = set(brand_ids)
            
            for influencer_id, collabs in influencer_collabs.items():
                # Filter collabs for brands in this category
                matching_collabs = [c for c in collabs if c["brand_id"] in category_set]
                
                if not matching_collabs:
                    continue
                
                # Calculate score components
                # 1. Max followers from matching collabs
                max_fl = max((c["followers"] for c in matching_collabs), default=0)
                follower_score = (max_fl / max_followers) if max_followers > 0 else 0
                
                # 2. Post ratio (posts / followers) - cap at 1.0
                total_posts = sum(c["post_count"] for c in matching_collabs)
                post_ratio = min(total_posts / max(max_fl, 1), 1.0)
                
                # 3. Number of collabs in this category
                collab_count = len(matching_collabs)
                collab_count_score = min(collab_count / 10, 1.0)  # Cap at 10 collabs
                
                # Combined score
                score = (follower_score * follower_w) + (post_ratio * post_ratio_w) + (collab_count_score * collab_count_w)
                
                # Get influencer details from first matching collab
                first_collab = matching_collabs[0]
                
                # Store influencer data
                infl_data = {
                    "influencer_id": influencer_id,
                    "platform": first_collab.get("platform", "instagram"),
                    "followers": max_fl,
                    "post_count": total_posts,
                    "collab_count": collab_count,
                    "brand_ids": [c["brand_id"] for c in matching_collabs],
                    "username": first_collab.get("username", ""),
                    "full_name": first_collab.get("full_name", ""),
                    "profile_image_url": first_collab.get("profile_image_url"),
                    "bio": first_collab.get("bio", ""),
                }
                
                if category not in category_influencers:
                    category_influencers[category] = []
                category_influencers[category].append((influencer_id, infl_data, score))
        
        # Step 5: Sort and store in Redis
        ttl_seconds = scoring_config.CATEGORY_RANKING_TTL_DAYS * 24 * 60 * 60
        
        stored_count = 0
        for category, infl_list in category_influencers.items():
            # Sort by score descending
            infl_list.sort(key=lambda x: x[2], reverse=True)
            
            # Store top influencers for this category (all of them)
            redis_key = f"{scoring_config.REDIS_PREFIX_CATEGORY}:{category}"
            
            # Store as JSON string list
            stored_data = [
                {
                    "influencer_id": infl_id,
                    "platform": data["platform"],
                    "followers": data["followers"],
                    "post_count": data["post_count"],
                    "collab_count": data["collab_count"],
                    "brand_ids": data["brand_ids"],
                    "score": round(score, 4),
                    "username": data.get("username", ""),
                    "full_name": data.get("full_name", ""),
                    "profile_image_url": data.get("profile_image_url"),
                    "bio": data.get("bio", ""),
                }
                for infl_id, data, score in infl_list
            ]
            
            redis_client.setex(redis_key, ttl_seconds, json.dumps(stored_data))
            stored_count += len(stored_data)
        
        # Also store an "all" category for fallback
        all_influencers = []
        for influencer_id, collabs in influencer_collabs.items():
            max_fl = max((c["followers"] for c in collabs), default=0)
            total_posts = sum(c["post_count"] for c in collabs)
            follower_score = (max_fl / max_followers) if max_followers > 0 else 0
            post_ratio = min(total_posts / max(max_fl, 1), 1.0)
            collab_count_score = min(len(collabs) / 10, 1.0)
            
            score = (follower_score * follower_w) + (post_ratio * post_ratio_w) + (collab_count_score * collab_count_w)
            
            # Get influencer details from first collab
            first_collab = collabs[0]
            
            all_influencers.append({
                "influencer_id": influencer_id,
                "platform": first_collab.get("platform", "instagram"),
                "followers": max_fl,
                "post_count": total_posts,
                "collab_count": len(collabs),
                "brand_ids": [c["brand_id"] for c in collabs],
                "score": round(score, 4),
                "username": first_collab.get("username", ""),
                "full_name": first_collab.get("full_name", ""),
                "profile_image_url": first_collab.get("profile_image_url"),
                "bio": first_collab.get("bio", ""),
            })
        
        all_influencers.sort(key=lambda x: x["score"], reverse=True)
        
        redis_key = f"{scoring_config.REDIS_PREFIX_CATEGORY}:{scoring_config.FALLBACK_CATEGORY}"
        redis_client.setex(redis_key, ttl_seconds, json.dumps(all_influencers))
        stored_count += len(all_influencers)
        
        elapsed = time.time() - start_time
        logger.info(f"Category rankings refresh completed in {elapsed:.2f}s. Stored {stored_count} influencers across {len(category_influencers)} categories")
        
        return {
            "status": "completed",
            "categories_processed": len(category_influencers),
            "total_influencers": stored_count,
            "elapsed_seconds": round(elapsed, 2),
        }

    def _generate_search_cache_key(self, categories: List[Dict], filters: Dict) -> str:
        """Generate cache key for search results."""
        key_data = {
            "categories": sorted(categories, key=lambda x: x.get("name", "")),
            "filters": filters,
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"{scoring_config.REDIS_PREFIX_SEARCH}:{hashlib.sha256(key_string.encode()).hexdigest()}"

    async def search_brand_collab(
        self,
        prompt: str,
        target_categories: List[Dict[str, Any]],
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """
        Search for influencers by brand collaborations.
        
        Args:
            prompt: User's search prompt
            target_categories: List of {name, weight} categories from LLM
            filters: Extracted filters (city, follower range, etc.)
            limit: Number of results to return
            offset: Pagination offset
            
        Returns:
            Tuple of (list of influencer results, total count)
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_search_cache_key(target_categories, filters)
        
        # Check cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            try:
                all_results = json.loads(cached_data)
                total = len(all_results)
                paginated = all_results[offset:offset + limit]
                logger.info(f"Cache hit for search. Returning {len(paginated)} of {total} results")
                return paginated, total
            except json.JSONDecodeError:
                pass
        
        # No cache - compute results
        category_names = [cat["name"] for cat in target_categories]
        category_weights = {cat["name"]: cat.get("weight", scoring_config.DEFAULT_CATEGORY_WEIGHT) for cat in target_categories}
        
        # Fetch influencers from each category
        all_influencers: Dict[str, Dict] = {}  # influencer_id -> infl_data with cumulative score
        
        for cat_name in category_names:
            redis_key = f"{scoring_config.REDIS_PREFIX_CATEGORY}:{cat_name}"
            data = redis_client.get(redis_key)
            
            if not data:
                continue
            
            try:
                infl_list = json.loads(data)
                cat_weight = category_weights.get(cat_name, scoring_config.DEFAULT_CATEGORY_WEIGHT)
                
                for infl in infl_list:
                    infl_id = infl["influencer_id"]
                    
                    # Calculate weighted score for this category
                    base_score = infl.get("score", 0)
                    weighted_score = base_score * cat_weight
                    
                    if infl_id not in all_influencers:
                        # First category this influencer appears in
                        all_influencers[infl_id] = {
                            "influencer_id": infl_id,
                            "platform": infl.get("platform", "instagram"),
                            "followers": infl.get("followers", 0),
                            "post_count": infl.get("post_count", 0),
                            "collab_count": infl.get("collab_count", 0),
                            "weighted_score": weighted_score,
                            "matched_categories": [cat_name],
                            "brand_ids": infl.get("brand_ids", []),
                            "username": infl.get("username", ""),
                            "full_name": infl.get("full_name", ""),
                            "profile_image_url": infl.get("profile_image_url"),
                            "bio": infl.get("bio", ""),
                        }
                    else:
                        # Already exists - add weighted score
                        existing = all_influencers[infl_id]
                        existing["weighted_score"] += weighted_score
                        existing["matched_categories"].append(cat_name)
                        existing["brand_ids"].extend(infl.get("brand_ids", []))
                        # Keep max followers/post_count across all collabs
                        existing["followers"] = max(existing["followers"], infl.get("followers", 0))
                        existing["post_count"] = max(existing["post_count"], infl.get("post_count", 0))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Redis data for category: {cat_name}")
        
        # If no categories matched, use fallback "all" category
        if not all_influencers:
            redis_key = f"{scoring_config.REDIS_PREFIX_CATEGORY}:{scoring_config.FALLBACK_CATEGORY}"
            data = redis_client.get(redis_key)
            
            if data:
                try:
                    infl_list = json.loads(data)
                    for infl in infl_list:
                        infl_id = infl["influencer_id"]
                        all_influencers[infl_id] = {
                            "influencer_id": infl_id,
                            "platform": infl.get("platform", "instagram"),
                            "followers": infl.get("followers", 0),
                            "post_count": infl.get("post_count", 0),
                            "collab_count": infl.get("collab_count", 0),
                            "weighted_score": infl.get("score", 0),
                            "matched_categories": [],
                            "brand_ids": infl.get("brand_ids", []),
                            "username": infl.get("username", ""),
                            "full_name": infl.get("full_name", ""),
                            "profile_image_url": infl.get("profile_image_url"),
                            "bio": infl.get("bio", ""),
                        }
                except json.JSONDecodeError:
                    pass
        
        # Apply additional filters (follower range, city, platform)
        filtered_results = []
        for infl_id, infl in all_influencers.items():
            # Follower range filter
            if filters.get("min_followers") and infl["followers"] < filters["min_followers"]:
                continue
            if filters.get("max_followers") and infl["followers"] > filters["max_followers"]:
                continue
            
            # Platform filter
            if filters.get("platform") and infl["platform"].lower() != filters["platform"].lower():
                continue
            
            filtered_results.append(infl)
        
        # Sort by weighted score
        filtered_results.sort(key=lambda x: x["weighted_score"], reverse=True)
        
        # Normalize scores to 0-1 range
        if filtered_results:
            max_score = max(infl["weighted_score"] for infl in filtered_results)
            min_score = min(infl["weighted_score"] for infl in filtered_results)
            score_range = max_score - min_score if max_score > min_score else 1
            
            for infl in filtered_results:
                infl["normalized_score"] = round((infl["weighted_score"] - min_score) / score_range, 4)
        
        # Cache the full results
        ttl_seconds = scoring_config.SEARCH_CACHE_TTL_DAYS * 24 * 60 * 60
        redis_client.setex(cache_key, ttl_seconds, json.dumps(filtered_results))
        
        total = len(filtered_results)
        paginated = filtered_results[offset:offset + limit]
        
        elapsed = time.time() - start_time
        logger.info(f"Brand collab search completed in {elapsed:.2f}s. Found {total} influencers, returning {len(paginated)}")
        
        return paginated, total


brand_collab_ranker = BrandCollabRanker()