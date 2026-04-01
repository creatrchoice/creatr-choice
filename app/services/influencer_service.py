"""Influencer discovery and analysis service."""
from typing import List, Optional
from app.models.influencer import (
    Influencer,
    InfluencerDetail,
    InfluencerSearchRequest,
    InfluencerSearchResponse,
)
from app.models.search import (
    NaturalLanguageSearchRequest,
    HybridSearchRequest,
    SearchFilters,
    InfluencerSearchResponse as EnhancedSearchResponse,
    InfluencerWithScore,
    BrandCollabSearchRequest,
    BrandCollabSearchResponse,
)
from app.models.categories import CategoryMetadata
from app.models.conversation import ChatSearchRequest, ChatSearchResponse
from app.services.hybrid_search import HybridSearchService
from app.services.nlp_agent import NLPAgent
from app.services.embedding_service import EmbeddingService
from app.services.category_discovery import CategoryDiscoveryService
from app.services.conversation_service import ConversationService
from app.services.brand_collab_ranker import brand_collab_ranker
from app.repositories.influencer_repository import InfluencerRepository
from app.models.influencer_data import InfluencerData


class InfluencerService:
    """Service for influencer discovery and analysis."""
    
    def __init__(self):
        """Initialize service."""
        self.hybrid_search = HybridSearchService()
        self.nlp_agent = NLPAgent()
        self.embedding_service = EmbeddingService()
        self.category_service = CategoryDiscoveryService()
        self.conversation_service = ConversationService()
        self.repository = InfluencerRepository()
    
    async def search_influencers(
        self, request: InfluencerSearchRequest
    ) -> InfluencerSearchResponse:
        """
        Search for influencers based on the provided criteria.
        """
        # Build search filters
        filters = SearchFilters(
            query=request.query,
            platform=request.platform,
            min_followers=request.min_followers,
            max_followers=request.max_followers,
            primary_category=request.category,
        )
        
        # Generate embedding if query provided
        vector_query = None
        if request.query:
            embedding_text = request.query
            vector_query = await self.embedding_service.generate_embedding(embedding_text)
        
        # Perform hybrid search
        results, search_time = await self.hybrid_search.search(
            query=request.query,
            vector_query=vector_query,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )
        
        # Get total count (approximate)
        total = await self.hybrid_search.get_total_count(
            query=request.query,
            vector_query=vector_query,
            filters=filters,
        )
        
        # Convert InfluencerWithScore to Influencer for response
        influencers = [
            Influencer(
                id=inf.id,
                username=inf.username,
                display_name=inf.display_name,
                platform=inf.platform,
                followers=inf.followers,
                following=inf.following,
                posts=inf.posts,
                profile_image_url=inf.profile_image_url,
                bio=inf.bio,
                verified=inf.verified,
                category=inf.category,
                engagement_rate=inf.engagement_rate,
                location=inf.location,
                average_views=inf.average_views,
                profile_url=inf.profile_url,
            )
            for inf in results
        ]
        
        return InfluencerSearchResponse(
            influencers=influencers,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total,
            relevance_scores=[inf.relevance_score for inf in results],
        )
    
    async def get_influencer_by_id(self, influencer_id: str) -> Optional[InfluencerDetail]:
        """
        Get detailed information about a specific influencer.
        """
        data = await self.repository.get_by_id(influencer_id)
        if not data:
            return None
        
        # Convert to InfluencerDetail
        return self._convert_to_influencer_detail(data)
    
    def _convert_to_influencer_detail(self, data: dict) -> InfluencerDetail:
        """Convert Cosmos DB document to InfluencerDetail."""
        from app.models.influencer import Platform
        
        platform = Platform.from_string(data.get("platform", "instagram"))
        
        return InfluencerDetail(
            id=str(data.get("id", "")),
            username=data.get("username", ""),
            display_name=data.get("name", data.get("username", "")),
            platform=platform,
            followers=data.get("followers_count", 0),
            following=None,
            posts=None,
            profile_image_url=data.get("picture"),
            bio=None,
            verified=False,
            category=data.get("primary_category", {}).get("name") if isinstance(data.get("primary_category"), dict) else data.get("primary_category"),
            engagement_rate=data.get("engagement_rate_value"),
            location=data.get("city"),
            average_views=data.get("avg_views_count"),
            profile_url=data.get("url"),
            content_topics=data.get("interest_categories", []),
        )
    
    async def analyze_influencer(
        self, username: str, platform: str
    ) -> Optional[InfluencerDetail]:
        """
        Analyze a new influencer by fetching data from the specified platform.
        
        TODO: Integrate with platform APIs (Twitter, Instagram, YouTube, etc.)
        """
        # Placeholder implementation
        # In a real application, this would:
        # 1. Fetch data from platform API
        # 2. Analyze engagement metrics
        # 3. Use AI to extract insights
        # 4. Store in database
        
        return InfluencerDetail(
            id=f"{platform}_{username}",
            username=username,
            display_name=username.title(),
            platform=platform,
            followers=10000,
            following=500,
            posts=200,
            bio=f"Influencer on {platform}",
            verified=False,
            category="General",
            engagement_rate=2.5,
        )
    
    async def get_trending_categories(self) -> List[str]:
        """
        Get list of trending influencer categories.
        """
        metadata = await self.category_service.get_categories()
        # Return top categories by count
        sorted_categories = sorted(
            metadata.interest_categories,
            key=lambda x: x.count,
            reverse=True
        )
        return [cat.name for cat in sorted_categories[:10]]
    
    async def search_nlp(self, request: NaturalLanguageSearchRequest) -> EnhancedSearchResponse:
        """
        Natural language search using NLP agent.
        """
        # Analyze query
        analysis = await self.nlp_agent.analyze_query(request.query)
        
        # Generate embedding for semantic search
        vector_query = await self.embedding_service.generate_embedding(request.query)
        
        # Perform hybrid search with extracted filters
        filters = SearchFilters(**analysis.extracted_filters.model_dump())
        
        results, search_time = await self.hybrid_search.search(
            query=request.query,
            vector_query=vector_query,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )
        
        total = await self.hybrid_search.get_total_count(
            query=request.query,
            vector_query=vector_query,
            filters=filters,
        )
        
        return EnhancedSearchResponse(
            influencers=results,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total,
            search_time_ms=search_time,
        )
    
    async def search_hybrid(self, request: HybridSearchRequest) -> EnhancedSearchResponse:
        """
        Advanced hybrid search.
        """
        filters = request.filters or SearchFilters()
        
        results, search_time = await self.hybrid_search.search(
            query=request.query,
            vector_query=request.vector_query,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )
        
        total = await self.hybrid_search.get_total_count(
            query=request.query,
            vector_query=request.vector_query,
            filters=filters,
        )
        
        return EnhancedSearchResponse(
            influencers=results,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total,
            search_time_ms=search_time,
        )
    
    async def get_categories(self) -> CategoryMetadata:
        """
        Get available categories from database.
        """
        return await self.category_service.get_categories()
    
    async def search_chat(self, request: ChatSearchRequest) -> ChatSearchResponse:
        """
        Conversational search with refinement support.
        
        Allows users to:
        - Start with an initial search query
        - Refine results with follow-up queries
        - Continue the conversation to narrow down results
        
        Example flow:
        1. User: "Find fitness influencers"
        2. System: Returns results
        3. User: "Show me only those in Mumbai"
        4. System: Returns refined results filtered by Mumbai
        5. User: "With more than 100K followers"
        6. System: Returns further refined results
        """
        return await self.conversation_service.search_chat(request)
    
    async def search_brand_collab(
        self, request: BrandCollabSearchRequest
    ) -> BrandCollabSearchResponse:
        """
        Search for influencers based on brand collaborations.
        
        This uses a brand-centric approach:
        1. LLM extracts target brand categories from prompt
        2. Find brands matching those categories
        3. Find brand_collaborations for those brands
        4. Score and rank influencers based on:
           - Category match (weighted by LLM)
           - Follower count
           - Post volume
           - Collaboration count
        """
        import time
        start_time = time.time()
        
        # Step 1: Analyze prompt to extract target categories with weights and filters
        analysis = await self.nlp_agent.analyze_query(request.prompt)
        
        # Step 2: Extract target categories and filters from analysis
        target_categories = []
        if analysis.target_categories:
            target_categories = [
                {"name": cat.name, "weight": cat.weight}
                for cat in analysis.target_categories
            ]
        
        # Fallback: if no target categories, use all categories with default weight
        if not target_categories:
            from app.config import scoring_config
            target_categories = [
                {"name": scoring_config.FALLBACK_CATEGORY, "weight": 1.0}
            ]
        
        # Extract filters from analysis
        filters = {}
        if analysis.extracted_filters:
            ef = analysis.extracted_filters
            if ef.min_followers:
                filters["min_followers"] = ef.min_followers
            if ef.max_followers:
                filters["max_followers"] = ef.max_followers
            if ef.platform:
                filters["platform"] = ef.platform
            if ef.city:
                filters["city"] = ef.city
        
        # Step 3: Search using brand collab ranker
        results, total = await brand_collab_ranker.search_brand_collab(
            prompt=request.prompt,
            target_categories=target_categories,
            filters=filters,
            limit=request.limit,
            offset=request.offset,
        )
        
        # Step 4: Fetch brand details for brand_collaborations field
        # TODO: Could optimize by caching brand names
        brand_info = {}
        for infl in results:
            for brand_id in infl.get("brand_ids", [])[:5]:  # Limit to 5 brands per influencer
                if brand_id not in brand_info:
                    brand_info[brand_id] = brand_id  # Placeholder - fetch real names in production
        
        # Convert to response model
        from app.models.search import InfluencerWithBrandScore, BrandCollaborationInfo
        from app.models.influencer import Platform
        
        influencers = []
        for infl in results:
            # Get brand collab info
            brand_collabs = []
            unique_brand_ids = list(set(infl.get("brand_ids", [])))
            for brand_id in unique_brand_ids[:5]:
                brand_collabs.append(BrandCollaborationInfo(
                    brand_id=brand_id,
                    brand_name=brand_info.get(brand_id, brand_id),
                    brand_categories=[]
                ))
            
            # Use actual data from Redis instead of influencer_id
            username = infl.get("username") or str(infl.get("influencer_id", ""))
            display_name = infl.get("full_name") or username
            
            influencers.append(InfluencerWithBrandScore(
                id=str(infl.get("influencer_id", "")),
                username=username,
                display_name=display_name,
                platform=Platform.from_string(infl.get("platform", "instagram")),
                followers=infl.get("followers", 0),
                following=None,
                posts=infl.get("post_count"),
                profile_image_url=infl.get("profile_image_url"),
                bio=infl.get("bio") or None,
                weighted_score=infl.get("normalized_score", infl.get("weighted_score", 0)),
                categories_matched=infl.get("matched_categories", []),
                brand_collaborations=brand_collabs,
            ))
        
        elapsed = time.time() - start_time
        
        return BrandCollabSearchResponse(
            influencers=influencers,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total,
            search_time_ms=round(elapsed * 1000, 2),
        )