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
    query: str = Field(..., description="User's search query or refinement request", example="Find fitness influencers in Mumbai")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for session management", example="conv-abc123")
    context: Optional[ConversationContext] = Field(None, description="Previous search context for refinement")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return", example=10)
    offset: int = Field(0, ge=0, description="Pagination offset", example=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find fitness influencers in Mumbai",
                "conversation_id": None,
                "context": None,
                "limit": 10,
                "offset": 0
            }
        }


class ChatSearchResponse(BaseModel):
    """Chat-based search response with conversation context."""
    influencers: List[InfluencerWithScore] = Field(..., description="List of influencers with relevance scores")
    total: int = Field(..., description="Total number of matching influencers", example=25)
    limit: int = Field(..., description="Number of results per page", example=10)
    offset: int = Field(..., description="Pagination offset", example=0)
    has_more: bool = Field(..., description="Whether there are more results available", example=True)
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds", example=320.1)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for session management", example="conv-abc123")
    applied_filters: SearchFilters = Field(..., description="Filters applied to this search")
    refinement_summary: Optional[str] = Field(None, description="Summary of how the query was refined", example="Added city filter: Mumbai, Added min_followers: 100000")
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up queries", example=["Filter by engagement rate", "Show only verified influencers"])
    
    class Config:
        json_schema_extra = {
            "example": {
                "influencers": [
                    {
                        "id": "123",
                        "username": "johndoe",
                        "relevance_score": 0.88
                    }
                ],
                "total": 25,
                "limit": 10,
                "offset": 0,
                "has_more": True,
                "search_time_ms": 320.1,
                "conversation_id": "conv-abc123",
                "applied_filters": {
                    "query": "fitness",
                    "city": "Mumbai",
                    "min_followers": 100000
                },
                "refinement_summary": "Added city filter: Mumbai, Added min_followers: 100000",
                "suggestions": ["Filter by engagement rate", "Show only verified influencers"]
            }
        }
