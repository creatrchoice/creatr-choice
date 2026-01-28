"""Search request and response models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.influencer import Influencer


class NaturalLanguageSearchRequest(BaseModel):
    """Natural language search request."""
    query: str = Field(..., description="Free-form text query describing the desired influencers", example="Find me a fitness micro-influencer in Mumbai who is affordable")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return", example=10)
    offset: int = Field(0, ge=0, description="Pagination offset", example=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Find me a fitness micro-influencer in Mumbai who is affordable",
                "limit": 10,
                "offset": 0
            }
        }


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
    relevance_score: float = Field(..., description="Relevance score from search (0-1, higher is more relevant)", example=0.95)


class InfluencerSearchResponse(BaseModel):
    """Enhanced search response with relevance scores."""
    influencers: List[InfluencerWithScore] = Field(..., description="List of influencers with relevance scores")
    total: int = Field(..., description="Total number of matching influencers", example=50)
    limit: int = Field(..., description="Number of results per page", example=10)
    offset: int = Field(..., description="Pagination offset", example=0)
    has_more: bool = Field(..., description="Whether there are more results available", example=True)
    search_time_ms: Optional[float] = Field(None, description="Search execution time in milliseconds", example=250.5)
    
    class Config:
        json_schema_extra = {
            "example": {
                "influencers": [
                    {
                        "id": "123",
                        "username": "johndoe",
                        "display_name": "John Doe",
                        "platform": "instagram",
                        "followers": 50000,
                        "relevance_score": 0.95
                    }
                ],
                "total": 50,
                "limit": 10,
                "offset": 0,
                "has_more": True,
                "search_time_ms": 250.5
            }
        }
