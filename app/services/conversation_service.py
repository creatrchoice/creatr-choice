"""Conversational search service for chat-like refinement."""
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from app.models.conversation import (
    ChatSearchRequest,
    ChatSearchResponse,
    ConversationContext,
    ConversationMessage,
    SearchFilters,
)
from app.models.search import InfluencerWithScore
from app.services.nlp_agent import NLPAgent
from app.services.hybrid_search import HybridSearchService
from app.services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for handling conversational search with refinement."""
    
    def __init__(self):
        """Initialize conversation service."""
        self.nlp_agent = NLPAgent()
        self.hybrid_search = HybridSearchService()
        self.embedding_service = EmbeddingService()
        # In-memory conversation storage (in production, use Redis or database)
        self.conversations: Dict[str, ConversationContext] = {}
    
    def _merge_filters(
        self, 
        previous_filters: Optional[SearchFilters], 
        new_filters: SearchFilters
    ) -> SearchFilters:
        """
        Merge previous filters with new refinement filters.
        
        Args:
            previous_filters: Filters from previous search
            new_filters: New filters from refinement query
        
        Returns:
            Merged SearchFilters
        """
        if not previous_filters:
            return new_filters
        
        # Start with previous filters
        merged = SearchFilters(
            query=previous_filters.query or new_filters.query,
            platform=new_filters.platform or previous_filters.platform,  # New takes precedence
            city=new_filters.city or previous_filters.city,  # New takes precedence
            creator_type=new_filters.creator_type or previous_filters.creator_type,  # New takes precedence
            primary_category=new_filters.primary_category or previous_filters.primary_category,  # New takes precedence
            language=new_filters.language or previous_filters.language,  # New takes precedence
        )
        
        # For numeric ranges, use more restrictive values
        if new_filters.min_followers is not None:
            if previous_filters.min_followers is None:
                merged.min_followers = new_filters.min_followers
            else:
                merged.min_followers = max(previous_filters.min_followers, new_filters.min_followers)
        
        if new_filters.max_followers is not None:
            if previous_filters.max_followers is None:
                merged.max_followers = new_filters.max_followers
            else:
                merged.max_followers = min(previous_filters.max_followers, new_filters.max_followers)
        
        if new_filters.min_engagement_rate is not None:
            if previous_filters.min_engagement_rate is None:
                merged.min_engagement_rate = new_filters.min_engagement_rate
            else:
                merged.min_engagement_rate = max(previous_filters.min_engagement_rate, new_filters.min_engagement_rate)
        
        if new_filters.max_engagement_rate is not None:
            if previous_filters.max_engagement_rate is None:
                merged.max_engagement_rate = new_filters.max_engagement_rate
            else:
                merged.max_engagement_rate = min(previous_filters.max_engagement_rate, new_filters.max_engagement_rate)
        
        if new_filters.min_avg_views is not None:
            if previous_filters.min_avg_views is None:
                merged.min_avg_views = new_filters.min_avg_views
            else:
                merged.min_avg_views = max(previous_filters.min_avg_views, new_filters.min_avg_views)
        
        if new_filters.max_avg_views is not None:
            if previous_filters.max_avg_views is None:
                merged.max_avg_views = new_filters.max_avg_views
            else:
                merged.max_avg_views = min(previous_filters.max_avg_views, new_filters.max_avg_views)
        
        if new_filters.min_ppc is not None:
            if previous_filters.min_ppc is None:
                merged.min_ppc = new_filters.min_ppc
            else:
                merged.min_ppc = max(previous_filters.min_ppc, new_filters.min_ppc)
        
        if new_filters.max_ppc is not None:
            if previous_filters.max_ppc is None:
                merged.max_ppc = new_filters.max_ppc
            else:
                merged.max_ppc = min(previous_filters.max_ppc, new_filters.max_ppc)
        
        # For lists (interest_categories), merge them
        if new_filters.interest_categories:
            if previous_filters.interest_categories:
                # Combine and deduplicate
                merged.interest_categories = list(set(
                    (previous_filters.interest_categories or []) + 
                    (new_filters.interest_categories or [])
                ))
            else:
                merged.interest_categories = new_filters.interest_categories
        elif previous_filters.interest_categories:
            # Preserve previous categories if no new ones
            merged.interest_categories = previous_filters.interest_categories
        
        return merged
    
    def _generate_refinement_summary(
        self,
        previous_filters: Optional[SearchFilters],
        new_filters: SearchFilters,
        merged_filters: SearchFilters
    ) -> str:
        """Generate a summary of how the search was refined."""
        changes = []
        
        if previous_filters:
            if new_filters.city and new_filters.city != previous_filters.city:
                changes.append(f"filtered by city: {new_filters.city}")
            
            if new_filters.min_followers and new_filters.min_followers != previous_filters.min_followers:
                changes.append(f"increased minimum followers to {new_filters.min_followers:,}")
            
            if new_filters.max_followers and new_filters.max_followers != previous_filters.max_followers:
                changes.append(f"decreased maximum followers to {new_filters.max_followers:,}")
            
            if new_filters.interest_categories:
                changes.append(f"added categories: {', '.join(new_filters.interest_categories)}")
        else:
            # First search
            if merged_filters.city:
                changes.append(f"filtered by city: {merged_filters.city}")
            if merged_filters.interest_categories:
                changes.append(f"categories: {', '.join(merged_filters.interest_categories)}")
            if merged_filters.min_followers:
                changes.append(f"minimum followers: {merged_filters.min_followers:,}")
        
        if changes:
            return "Refined search: " + ", ".join(changes)
        return "Applied your search criteria"
    
    def _generate_suggestions(
        self,
        filters: SearchFilters,
        total: int
    ) -> List[str]:
        """Generate suggested follow-up queries."""
        suggestions = []
        
        if total > 50:
            suggestions.append("Narrow down by city or category")
            suggestions.append("Add minimum followers requirement")
        
        if not filters.city:
            suggestions.append("Filter by specific city")
        
        if not filters.min_engagement_rate:
            suggestions.append("Show only high engagement influencers")
        
        if not filters.max_ppc:
            suggestions.append("Filter by budget/price range")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    async def search_chat(self, request: ChatSearchRequest) -> ChatSearchResponse:
        """
        Perform conversational search with refinement support.
        
        Args:
            request: Chat search request with optional context
        
        Returns:
            ChatSearchResponse with results and conversation context
        """
        # Get or create conversation context
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # If conversation_id provided, get stored context
        # Otherwise use provided context or start fresh
        if request.conversation_id and request.conversation_id in self.conversations:
            context = self.conversations[request.conversation_id]
        elif request.context:
            context = request.context
        else:
            context = None
        
        # Analyze the query
        analysis = await self.nlp_agent.analyze_query(request.query)
        new_filters = SearchFilters(**analysis.extracted_filters.model_dump())
        
        # Merge with previous filters if this is a refinement
        if context and context.previous_filters:
            merged_filters = self._merge_filters(context.previous_filters, new_filters)
            refinement_summary = self._generate_refinement_summary(
                context.previous_filters,
                new_filters,
                merged_filters
            )
        else:
            merged_filters = new_filters
            refinement_summary = None
        
        # Generate embedding for semantic search
        search_query = request.query if not context or not context.previous_query else f"{context.previous_query} {request.query}"
        vector_query = await self.embedding_service.generate_embedding(search_query)
        
        # Perform hybrid search
        results, search_time = await self.hybrid_search.search(
            query=search_query,
            vector_query=vector_query,
            filters=merged_filters,
            limit=request.limit,
            offset=request.offset,
        )
        
        # Get total count
        total = await self.hybrid_search.get_total_count(
            query=search_query,
            vector_query=vector_query,
            filters=merged_filters,
        )
        
        # Generate suggestions
        suggestions = self._generate_suggestions(merged_filters, total)
        
        # Update conversation context
        updated_context = ConversationContext(
            previous_filters=merged_filters,
            previous_results_count=total,
            previous_query=search_query,
            conversation_history=[
                ConversationMessage(
                    role="user",
                    content=request.query,
                    timestamp=datetime.utcnow().isoformat()
                ),
                ConversationMessage(
                    role="assistant",
                    content=f"Found {total} influencers matching your criteria",
                    timestamp=datetime.utcnow().isoformat()
                )
            ]
        )
        
        # Store context
        if context:
            updated_context.conversation_history = context.conversation_history + updated_context.conversation_history
        self.conversations[conversation_id] = updated_context
        
        return ChatSearchResponse(
            influencers=results,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total,
            search_time_ms=search_time,
            conversation_id=conversation_id,
            applied_filters=merged_filters,
            refinement_summary=refinement_summary,
            suggestions=suggestions,
        )
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context by ID."""
        return self.conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation context."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
