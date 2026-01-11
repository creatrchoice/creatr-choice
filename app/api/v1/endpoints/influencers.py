"""Influencer discovery endpoints."""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel

from app.models.influencer import (
    Influencer,
    InfluencerSearchRequest,
    InfluencerSearchResponse,
    InfluencerDetail,
)
from app.models.search import (
    NaturalLanguageSearchRequest,
    HybridSearchRequest,
    InfluencerSearchResponse as EnhancedSearchResponse,
)
from app.models.conversation import ChatSearchRequest, ChatSearchResponse
from app.models.categories import CategoryMetadata
from app.services.influencer_service import InfluencerService


class AnalyzeInfluencerRequest(BaseModel):
    """Request model for influencer analysis."""
    username: str
    platform: str

router = APIRouter()
influencer_service = InfluencerService()


@router.get("/", response_model=InfluencerSearchResponse)
async def search_influencers(
    query: Optional[str] = Query(None, description="Search query for influencers"),
    platform: Optional[str] = Query(None, description="Social media platform (twitter, instagram, youtube)"),
    min_followers: Optional[int] = Query(None, description="Minimum number of followers"),
    max_followers: Optional[int] = Query(None, description="Maximum number of followers"),
    category: Optional[str] = Query(None, description="Influencer category/niche"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Search and discover influencers based on various criteria.
    
    - **query**: Search by name, username, or bio keywords
    - **platform**: Filter by social media platform
    - **min_followers**: Minimum follower count
    - **max_followers**: Maximum follower count
    - **category**: Filter by influencer category/niche
    """
    search_request = InfluencerSearchRequest(
        query=query,
        platform=platform,
        min_followers=min_followers,
        max_followers=max_followers,
        category=category,
        limit=limit,
        offset=offset,
    )
    
    results = await influencer_service.search_influencers(search_request)
    return results


@router.get("/trending/categories", response_model=List[str])
async def get_trending_categories():
    """Get list of trending influencer categories."""
    categories = await influencer_service.get_trending_categories()
    return categories


@router.get("/categories", response_model=CategoryMetadata)
async def get_categories():
    """
    Get all available categories, cities, creator types, and platforms.
    
    This endpoint returns metadata about all available filter options,
    including counts and statistics for each category.
    """
    metadata = await influencer_service.get_categories()
    return metadata


@router.get("/{influencer_id}", response_model=InfluencerDetail)
async def get_influencer(influencer_id: str):
    """
    Get detailed information about a specific influencer.
    
    - **influencer_id**: Unique identifier for the influencer
    """
    influencer = await influencer_service.get_influencer_by_id(influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return influencer


@router.post("/analyze", response_model=InfluencerDetail)
async def analyze_influencer(
    request: AnalyzeInfluencerRequest = Body(..., description="Influencer analysis request"),
):
    """
    Analyze a new influencer by username and platform.
    
    This endpoint will fetch and analyze influencer data from the specified platform.
    """
    influencer = await influencer_service.analyze_influencer(request.username, request.platform)
    if not influencer:
        raise HTTPException(
            status_code=404,
            detail=f"Influencer '{request.username}' not found on {request.platform}",
        )
    return influencer


@router.post("/search/nlp", response_model=EnhancedSearchResponse)
async def search_nlp(request: NaturalLanguageSearchRequest):
    """
    Natural language search for influencers.
    
    Accepts free-form text queries and uses AI to understand the intent
    and extract search parameters. Returns ranked influencers with relevance scores.
    
    Example queries:
    - "Find me a fitness micro-influencer in Mumbai who is affordable"
    - "I need Gen-Z fashion creators with high engagement"
    - "Show me tech influencers with over 100K followers"
    """
    results = await influencer_service.search_nlp(request)
    return results


@router.post("/search/hybrid", response_model=EnhancedSearchResponse)
async def search_hybrid(request: HybridSearchRequest):
    """
    Advanced hybrid search combining keyword, vector, and filter search.
    
    Supports:
    - Keyword search query
    - Vector similarity search (provide embedding)
    - Explicit filters (platform, city, followers, etc.)
    """
    results = await influencer_service.search_hybrid(request)
    return results


@router.post("/search/chat", response_model=ChatSearchResponse)
async def search_chat(request: ChatSearchRequest):
    """
    Conversational search with refinement support - Chat-like interface.
    
    This endpoint allows users to have a conversation to refine their search results.
    You can start with a query and then make follow-up refinements.
    
    **First Query Example:**
    ```json
    {
      "query": "Find fitness influencers in Mumbai",
      "limit": 10
    }
    ```
    
    **Refinement Query Example:**
    ```json
    {
      "query": "Show me only those with more than 100K followers",
      "conversation_id": "abc-123",
      "context": {
        "previous_filters": { ... },
        "previous_query": "Find fitness influencers in Mumbai"
      },
      "limit": 10
    }
    ```
    
    **Refinement Examples:**
    - "Show me only those in Mumbai" → Adds city filter
    - "With more than 100K followers" → Adds min_followers filter
    - "Only micro-influencers" → Sets creator_type and max_followers
    - "With high engagement" → Adds min_engagement_rate filter
    - "More affordable" → Decreases max_ppc
    - "Add fashion category" → Adds Fashion to interest_categories
    
    The system maintains conversation context and merges new filters with previous ones.
    """
    results = await influencer_service.search_chat(request)
    return results
