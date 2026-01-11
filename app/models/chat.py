"""Chat-based search models for conversational influencer discovery."""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.search import SearchFilters, InfluencerWithScore


class ChatMessage(BaseModel):
    """Single message in a conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ConversationContext(BaseModel):
    """Context from previous search results."""
    previous_filters: Optional[SearchFilters] = Field(None, description="Previous search filters")
    previous_query: Optional[str] = Field(None, description="Previous search query")
    previous_results_count: Optional[int] = Field(None, description="Number of results from previous search")
    mentioned_influencers: Optional[List[str]] = Field(None, description="Influencer IDs or usernames mentioned")
    refinement_intent: Optional[str] = Field(None, description="User's intent for refinement")


class ChatSearchRequest(BaseModel):
    """Chat-based search request with conversation context."""
    message: str = Field(..., description="User's current message/query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for maintaining context")
    previous_filters: Optional[SearchFilters] = Field(None, description="Previous search filters to refine")
    previous_query: Optional[str] = Field(None, description="Previous search query")
    previous_results: Optional[List[InfluencerWithScore]] = Field(None, description="Previous search results for context")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Pagination offset")


class ChatSearchResponse(BaseModel):
    """Chat-based search response with conversation context."""
    influencers: List[InfluencerWithScore]
    total: int
    limit: int
    offset: int
    has_more: bool
    search_time_ms: Optional[float] = None
    conversation_id: Optional[str] = Field(None, description="Conversation ID for next request")
    suggested_refinements: Optional[List[str]] = Field(None, description="Suggested ways to refine the search")
    applied_filters: Optional[SearchFilters] = Field(None, description="Filters that were applied to this search")
    search_intent: Optional[str] = Field(None, description="Understanding of the search intent")
