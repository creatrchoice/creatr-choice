"""Category discovery service to extract available categories from Cosmos DB."""
from typing import List, Dict, Set, Optional
from collections import defaultdict
from app.db.cosmos_db import CosmosDBClient
from app.models.categories import CategoryMetadata, CategoryStatistic
from app.core.config import settings


class CategoryDiscoveryService:
    """Service to discover and cache available categories."""
    
    def __init__(self):
        """Initialize category discovery service."""
        self.cosmos_client = CosmosDBClient()
        self._cache: Optional[CategoryMetadata] = None
    
    async def refresh_cache(self) -> CategoryMetadata:
        """
        Refresh category cache from Cosmos DB.
        
        Returns:
            CategoryMetadata with all discovered categories
        """
        await self.cosmos_client.connect_async()
        
        # Query only necessary fields to extract categories (much faster)
        # Use a sample of records to build cache quickly (10K is enough for categories)
        query = "SELECT c.interest_categories, c.primary_category, c.city, c.creator_type, c.platform, c.engagement_rate_value, c.followers_count FROM c OFFSET 0 LIMIT 10000"
        
        try:
            influencers = await self.cosmos_client.query_items_async(query)
        except Exception as e:
            # If query fails, try with synchronous client as fallback
            self.cosmos_client.connect()
            influencers = self.cosmos_client.query_items(query)
        
        # Extract unique values
        interest_categories_set: Set[str] = set()
        primary_categories_set: Set[str] = set()
        cities_set: Set[str] = set()
        creator_types_set: Set[str] = set()
        platforms_set: Set[str] = set()
        
        # Statistics
        category_counts: Dict[str, int] = defaultdict(int)
        category_engagement: Dict[str, List[float]] = defaultdict(list)
        category_followers: Dict[str, List[int]] = defaultdict(list)
        
        primary_category_counts: Dict[str, int] = defaultdict(int)
        primary_category_engagement: Dict[str, List[float]] = defaultdict(list)
        
        for influencer in influencers:
            # Extract interest categories
            if "interest_categories" in influencer and isinstance(influencer["interest_categories"], list):
                for cat in influencer["interest_categories"]:
                    if cat:
                        interest_categories_set.add(str(cat))
                        category_counts[cat] += 1
                        if "engagement_rate_value" in influencer and influencer["engagement_rate_value"]:
                            category_engagement[cat].append(influencer["engagement_rate_value"])
                        if "followers_count" in influencer and influencer["followers_count"]:
                            category_followers[cat].append(influencer["followers_count"])
            
            # Extract primary category
            if "primary_category" in influencer and influencer["primary_category"]:
                if isinstance(influencer["primary_category"], dict):
                    primary_cat = influencer["primary_category"].get("name")
                else:
                    primary_cat = str(influencer["primary_category"])
                
                if primary_cat:
                    primary_categories_set.add(primary_cat)
                    primary_category_counts[primary_cat] += 1
                    if "engagement_rate_value" in influencer and influencer["engagement_rate_value"]:
                        primary_category_engagement[primary_cat].append(influencer["engagement_rate_value"])
            
            # Extract city
            if "city" in influencer and influencer["city"]:
                cities_set.add(str(influencer["city"]))
            
            # Extract creator type
            if "creator_type" in influencer and influencer["creator_type"]:
                creator_types_set.add(str(influencer["creator_type"]))
            
            # Extract platform
            if "platform" in influencer and influencer["platform"]:
                platforms_set.add(str(influencer["platform"]))
        
        # Build category statistics
        interest_category_stats = []
        for cat in sorted(interest_categories_set):
            count = category_counts.get(cat, 0)
            engagements = category_engagement.get(cat, [])
            followers = category_followers.get(cat, [])
            
            avg_engagement = sum(engagements) / len(engagements) if engagements else None
            avg_followers = sum(followers) / len(followers) if followers else None
            min_followers = min(followers) if followers else None
            max_followers = max(followers) if followers else None
            
            interest_category_stats.append(CategoryStatistic(
                name=cat,
                count=count,
                avg_engagement_rate=avg_engagement,
                avg_followers=avg_followers,
                min_followers=min_followers,
                max_followers=max_followers
            ))
        
        primary_category_stats = []
        for cat in sorted(primary_categories_set):
            count = primary_category_counts.get(cat, 0)
            engagements = primary_category_engagement.get(cat, [])
            
            avg_engagement = sum(engagements) / len(engagements) if engagements else None
            
            primary_category_stats.append(CategoryStatistic(
                name=cat,
                count=count,
                avg_engagement_rate=avg_engagement
            ))
        
        # Build metadata
        metadata = CategoryMetadata(
            interest_categories=interest_category_stats,
            primary_categories=primary_category_stats,
            cities=sorted(list(cities_set)),
            creator_types=sorted(list(creator_types_set)),
            platforms=sorted(list(platforms_set)),
            total_influencers=len(influencers)
        )
        
        self._cache = metadata
        return metadata
    
    async def get_categories(self) -> CategoryMetadata:
        """
        Get category metadata (from cache or refresh if needed).
        
        Returns:
            CategoryMetadata
        """
        if self._cache is None:
            return await self.refresh_cache()
        return self._cache
    
    async def get_all_categories(self) -> List[str]:
        """Get all unique interest categories."""
        metadata = await self.get_categories()
        return [cat.name for cat in metadata.interest_categories]
    
    async def get_primary_categories(self) -> List[str]:
        """Get all unique primary categories."""
        metadata = await self.get_categories()
        return [cat.name for cat in metadata.primary_categories]
    
    async def get_cities(self) -> List[str]:
        """Get all unique cities."""
        metadata = await self.get_categories()
        return metadata.cities
    
    async def get_creator_types(self) -> List[str]:
        """Get all unique creator types."""
        metadata = await self.get_categories()
        return metadata.creator_types
    
    async def get_platforms(self) -> List[str]:
        """Get all unique platforms."""
        metadata = await self.get_categories()
        return metadata.platforms
