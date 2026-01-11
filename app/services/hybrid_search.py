"""Hybrid search engine combining keyword, vector, and semantic search."""
from typing import List, Dict, Any, Optional
import time
from app.db.azure_search_store import AzureSearchStore
from app.db.cosmos_db import CosmosDBClient
from app.models.search import SearchFilters, InfluencerWithScore
from app.models.influencer import Influencer, Platform
from app.core.config import settings


class HybridSearchService:
    """Hybrid search service."""
    
    def __init__(self):
        """Initialize hybrid search service."""
        self.search_store = AzureSearchStore()
        self.cosmos_client = CosmosDBClient()
    
    async def search(
        self,
        query: Optional[str] = None,
        vector_query: Optional[List[float]] = None,
        filters: Optional[SearchFilters] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[InfluencerWithScore], float]:
        """
        Perform hybrid search.
        
        Args:
            query: Keyword search query
            vector_query: Vector embedding for similarity search
            filters: Search filters
            limit: Number of results
            offset: Pagination offset
        
        Returns:
            Tuple of (results, search_time_ms)
        """
        start_time = time.time()
        
        # Convert filters to dictionary
        filter_dict = {}
        if filters:
            filter_dict = {
                "platform": filters.platform,
                "city": filters.city,
                "creator_type": filters.creator_type,
                "min_followers": filters.min_followers,
                "max_followers": filters.max_followers,
                "min_engagement_rate": filters.min_engagement_rate,
                "max_engagement_rate": filters.max_engagement_rate,
                "min_avg_views": filters.min_avg_views,
                "max_avg_views": filters.max_avg_views,
                "interest_categories": filters.interest_categories,
                "primary_category": filters.primary_category,
            }
        
        # Perform hybrid search
        search_results = self.search_store.hybrid_search(
            query=query,
            vector_query=vector_query,
            filters=filter_dict,
            top=limit + offset  # Get more to handle offset
        )
        
        # Apply offset
        paginated_results = search_results[offset:offset + limit]
        
        # Convert to InfluencerWithScore
        influencers = []
        for result in paginated_results:
            influencer = self._convert_search_result_to_influencer(result)
            if influencer:
                influencers.append(influencer)
        
        search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return influencers, search_time
    
    def _convert_search_result_to_influencer(
        self, result: Dict[str, Any]
    ) -> Optional[InfluencerWithScore]:
        """
        Convert Azure AI Search result to InfluencerWithScore.
        
        Args:
            result: Search result from Azure AI Search
        
        Returns:
            InfluencerWithScore or None
        """
        try:
            # Extract score
            score = result.get("@search.score", 0.0)
            
            # Extract fields
            influencer_id = str(result.get("id", result.get("influencer_id", "")))
            username = result.get("username", "")
            name = result.get("name", username)
            platform_str = result.get("platform", "instagram")
            
            # Convert platform
            try:
                platform = Platform.from_string(platform_str)
            except:
                platform = Platform.INSTAGRAM
            
            followers = result.get("followers_count", 0)
            avg_views = result.get("avg_views_count", None)
            profile_url = result.get("url", None)
            
            # Build influencer
            influencer = InfluencerWithScore(
                id=influencer_id,
                username=username,
                display_name=name,
                platform=platform,
                followers=followers,
                following=None,
                posts=None,
                profile_image_url=result.get("picture"),
                bio=None,
                verified=False,
                category=result.get("primary_category"),
                engagement_rate=result.get("engagement_rate_value"),
                location=result.get("city"),
                average_views=avg_views,
                profile_url=profile_url,
                relevance_score=score
            )
            
            return influencer
        
        except Exception as e:
            print(f"Error converting search result: {e}")
            return None
    
    async def get_total_count(
        self,
        query: Optional[str] = None,
        vector_query: Optional[List[float]] = None,
        filters: Optional[SearchFilters] = None,
    ) -> int:
        """
        Get total count of matching results (approximate).
        
        Args:
            query: Keyword search query
            vector_query: Vector embedding
            filters: Search filters
        
        Returns:
            Approximate total count
        """
        # For now, return a large number or implement proper counting
        # Azure AI Search doesn't provide exact counts efficiently
        results, _ = await self.search(query, vector_query, filters, limit=1000, offset=0)
        return len(results) if len(results) < 1000 else 1000  # Approximate
