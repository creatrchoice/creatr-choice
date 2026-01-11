"""Conversational search models for chat-like refinement."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.models.search import SearchFilters, InfluencerWithScore


class ConversationMessage(BaseModel):
    """A message in the conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ConversationContext(BaseModel):
    """Context from previous search results."""
    previous_filters: Optional[SearchFilters] = Field(None, description="Previous search filters")
    previous_results_count: Optional[int] = Field(None, description="Number of results from previous search")
    previous_query: Optional[str] = Field(None, description="Previous search query")
    conversation_history: List[ConversationMessage] = Field(default_factory=list, description="Conversation history")


class ChatSearchRequest(BaseModel):
    """Chat-based search request with conversation context."""
    query: str = Field(..., description="User's search query or refinement request")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for session management")
    context: Optional[ConversationContext] = Field(None, description="Previous search context for refinement")
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
    conversation_id: Optional[str] = Field(None, description="Conversation ID for session management")
    applied_filters: SearchFilters = Field(..., description="Filters applied to this search")
    refinement_summary: Optional[str] = Field(None, description="Summary of how the query was refined")
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up queries")
