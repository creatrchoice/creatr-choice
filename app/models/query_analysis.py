"""Query analysis models for NLP agent."""
from pydantic import BaseModel, Field
from typing import Optional, List


class ExtractedFilters(BaseModel):
    """Filters extracted from natural language query."""
    platform: Optional[str] = Field(None, description="Social media platform")
    interest_categories: Optional[List[str]] = Field(None, description="Interest categories")
    primary_category: Optional[str] = Field(None, description="Primary category")
    city: Optional[str] = Field(None, description="City location")
    creator_type: Optional[str] = Field(None, description="Creator type (macro, micro, nano)")
    min_followers: Optional[int] = Field(None, description="Minimum followers")
    max_followers: Optional[int] = Field(None, description="Maximum followers")
    min_engagement_rate: Optional[float] = Field(None, description="Minimum engagement rate")
    max_engagement_rate: Optional[float] = Field(None, description="Maximum engagement rate")
    min_avg_views: Optional[int] = Field(None, description="Minimum average views per post")
    max_avg_views: Optional[int] = Field(None, description="Maximum average views per post")
    max_ppc: Optional[int] = Field(None, description="Maximum price per collaboration")
    min_ppc: Optional[int] = Field(None, description="Minimum price per collaboration")
    language: Optional[str] = Field(None, description="Content language")


class QueryAnalysisResult(BaseModel):
    """Result of NLP query analysis."""
    search_intent: str = Field(..., description="Understanding of what the user is looking for")
    extracted_filters: ExtractedFilters = Field(..., description="Extracted search parameters")
    suggested_categories: Optional[List[str]] = Field(None, description="Suggested categories if query is ambiguous")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of extraction")
    original_query: str = Field(..., description="Original user query")
