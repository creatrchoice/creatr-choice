"""Scoring configuration for brand collab search."""

INFLUENCER_SCORING = {
    "follower_weight": 0.60,
    "post_ratio_weight": 0.30,
    "collab_count_weight": 0.10,
}

CATEGORY_RANKING_TTL_DAYS = 7
SEARCH_CACHE_TTL_DAYS = 1

REDIS_PREFIX_CATEGORY = "category_rankings"
REDIS_PREFIX_SEARCH = "search_cache"

FALLBACK_CATEGORY = "all"
DEFAULT_CATEGORY_WEIGHT = 0.5