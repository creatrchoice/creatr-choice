"""Search request and response models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.influencer import Influencer


class NaturalLanguageSearchRequest(BaseModel):
    """Natural language search request."""
    query: str = Field(..., description="Free-form text query describing the desired influencers")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SearchFilters(BaseModel):
    """Extracted search filters from NLP query."""
    query: Optional[str] = None
    platform: Optional[str] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    min_engagement_rate: Optional[float] = None
    max_engagement_rate: Optional[float] = None
    min_avg_views: Optional[int] = Field(None, description="Minimum average views per post")
    max_avg_views: Optional[int] = Field(None, description="Maximum average views per post")
    interest_categories: Optional[List[str]] = None
    primary_category: Optional[str] = None
    city: Optional[str] = None
    creator_type: Optional[str] = None
    max_ppc: Optional[int] = None
    min_ppc: Optional[int] = None
    language: Optional[str] = None


class HybridSearchRequest(BaseModel):
    """Advanced hybrid search request."""
    query: Optional[str] = Field(None, description="Semantic search query")
    filters: Optional[SearchFilters] = Field(None, description="Explicit filters")
    vector_query: Optional[List[float]] = Field(None, description="Vector embedding for similarity search")
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class InfluencerWithScore(Influencer):
    """Influencer with relevance score."""
    relevance_score: float = Field(..., description="Relevance score from search")


class InfluencerSearchResponse(BaseModel):
    """Enhanced search response with relevance scores."""
    influencers: List[InfluencerWithScore]
    total: int
    limit: int
    offset: int
    has_more: bool
    search_time_ms: Optional[float] = None
