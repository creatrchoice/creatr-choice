"""Influencer discovery endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Query, Body, Path, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

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
    username: str = Field(..., description="Username/handle of the influencer", example="johndoe")
    platform: str = Field(..., description="Social media platform", example="instagram")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "platform": "instagram"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Influencer not found"
            }
        }


logger = logging.getLogger(__name__)

router = APIRouter()
influencer_service = InfluencerService()


@router.get(
    "/",
    response_model=InfluencerSearchResponse,
    summary="Search Influencers",
    description="Search and discover influencers based on various criteria including query, platform, follower count, and category.",
    responses={
        200: {
            "description": "Successful response with influencer search results",
            "content": {
                "application/json": {
                    "example": {
                        "influencers": [
                            {
                                "id": "123",
                                "username": "johndoe",
                                "display_name": "John Doe",
                                "platform": "instagram",
                                "followers": 50000,
                                "following": 1000,
                                "posts": 500,
                                "profile_image_url": "https://example.com/image.jpg",
                                "bio": "Fitness enthusiast",
                                "verified": False,
                                "category": "Fitness",
                                "engagement_rate": 4.5,
                                "location": "Mumbai, India"
                            }
                        ],
                        "total": 100,
                        "limit": 10,
                        "offset": 0,
                        "has_more": True
                    }
                }
            }
        }
    },
    tags=["influencers"]
)
async def search_influencers(
    query: Optional[str] = Query(None, description="Search query for influencers (name, username, or bio keywords)", example="fitness"),
    platform: Optional[str] = Query(None, description="Social media platform", example="instagram"),
    min_followers: Optional[int] = Query(None, description="Minimum number of followers", example=10000),
    max_followers: Optional[int] = Query(None, description="Maximum number of followers", example=100000),
    category: Optional[str] = Query(None, description="Influencer category/niche", example="Fitness"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return", example=10),
    offset: int = Query(0, ge=0, description="Pagination offset", example=0),
):
    """
    Search and discover influencers based on various criteria.
    
    This endpoint allows you to search for influencers using multiple filters:
    
    - **query**: Search by name, username, or bio keywords
    - **platform**: Filter by social media platform (twitter, instagram, youtube, tiktok, linkedin)
    - **min_followers**: Minimum follower count
    - **max_followers**: Maximum follower count
    - **category**: Filter by influencer category/niche
    - **limit**: Number of results per page (1-100)
    - **offset**: Pagination offset for retrieving more results
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


@router.get(
    "/trending/categories",
    response_model=List[str],
    summary="Get Trending Categories",
    description="Retrieve a list of currently trending influencer categories based on popularity and engagement metrics.",
    responses={
        200: {
            "description": "List of trending category names",
            "content": {
                "application/json": {
                    "example": ["Fitness", "Fashion", "Technology", "Food", "Travel"]
                }
            }
        }
    },
    tags=["influencers"]
)
async def get_trending_categories():
    """
    Get list of trending influencer categories.
    
    Returns the most popular and engaging categories based on current data.
    Categories are ranked by factors such as number of influencers, average engagement rates, and recent activity.
    """
    categories = await influencer_service.get_trending_categories()
    return categories


@router.get(
    "/categories",
    response_model=CategoryMetadata,
    summary="Get All Categories Metadata",
    description="Retrieve comprehensive metadata about all available filter options including categories, cities, creator types, and platforms with statistics.",
    responses={
        200: {
            "description": "Category metadata with statistics",
            "content": {
                "application/json": {
                    "example": {
                        "interest_categories": [
                            {"name": "Fitness", "count": 500, "avg_engagement_rate": 4.5, "avg_followers": 50000}
                        ],
                        "primary_categories": [
                            {"name": "Lifestyle", "count": 300, "avg_engagement_rate": 3.8}
                        ],
                        "cities": ["Mumbai", "Delhi", "Bangalore"],
                        "creator_types": ["Micro-influencer", "Macro-influencer", "Celebrity"],
                        "platforms": ["instagram", "twitter", "youtube"],
                        "total_influencers": 10000
                    }
                }
            }
        }
    },
    tags=["influencers"]
)
async def get_categories():
    """
    Get all available categories, cities, creator types, and platforms.
    
    This endpoint returns comprehensive metadata about all available filter options,
    including counts and statistics for each category. Use this to discover what
    filters are available before performing searches.
    
    Returns:
    - **interest_categories**: List of interest categories with statistics
    - **primary_categories**: List of primary categories with statistics
    - **cities**: List of available cities
    - **creator_types**: List of creator types (e.g., Micro-influencer, Macro-influencer)
    - **platforms**: List of supported platforms
    - **total_influencers**: Total number of influencers in the database
    """
    metadata = await influencer_service.get_categories()
    return metadata


@router.get(
    "/fetch-details",
    summary="Fetch Influencer Details",
    description="Fetch Instagram posts and details for a specific influencer username.",
    responses={
        200: {
            "description": "Successfully fetched influencer details",
            "content": {
                "application/json": {
                    "example": {
                        "result": {
                            "edges": [
                                {
                                    "node": {
                                        "code": "ABC123",
                                        "pk": "123456789",
                                        "user": {
                                            "username": "keke",
                                            "full_name": "Keke",
                                            "pk": "123456789",
                                            "is_verified": False
                                        },
                                        "like_count": 1000,
                                        "comment_count": 50
                                    }
                                }
                            ],
                            "page_info": {
                                "has_next_page": True,
                                "end_cursor": "QVFBS..."
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid parameters",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["influencers"]
)
async def get_influencer_details(
    username: str = Query(..., description="Instagram username (without @)", example="keke"),
    max_id: Optional[str] = Query(None, description="Pagination cursor from previous request", example="QVFBS..."),
):
    """
    Fetch influencer details and posts from Instagram.
    
    This endpoint fetches posts and profile information for a specific Instagram username.
    It uses the Instagram API to retrieve the latest posts and associated metadata.
    
    **Parameters:**
    - **username**: Instagram username (without @ symbol)
    - **max_id**: Optional pagination cursor to fetch next page of results
    
    **Response:**
    Returns the raw Instagram API response containing:
    - Posts data (edges array with post nodes)
    - User information
    - Pagination info (has_next_page, end_cursor)
    - Engagement metrics (likes, comments, views)
    
    **Pagination:**
    Use the `end_cursor` from the response as `max_id` in the next request to fetch more posts.
    
    **Example Request:**
    ```
    GET /api/v1/influencers/fetch-details?username=keke
    ```
    
    **Example Request with Pagination:**
    ```
    GET /api/v1/influencers/fetch-details?username=keke&max_id=QVFBS...
    ```
    
    **Note**: This endpoint requires a valid RAPIDAPI_KEY to be configured.
    """
    try:
        data = await fetch_influencer_posts(username, max_id)
        return data
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error in get_influencer_details: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch influencer details: {str(error)}",
        )


@router.get(
    "/{influencer_id}",
    response_model=InfluencerDetail,
    summary="Get Influencer Details",
    description="Retrieve detailed information about a specific influencer by their unique ID.",
    responses={
        200: {
            "description": "Detailed influencer information",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123",
                        "username": "johndoe",
                        "display_name": "John Doe",
                        "platform": "instagram",
                        "followers": 50000,
                        "following": 1000,
                        "posts": 500,
                        "profile_image_url": "https://example.com/image.jpg",
                        "bio": "Fitness enthusiast",
                        "verified": False,
                        "category": "Fitness",
                        "engagement_rate": 4.5,
                        "location": "Mumbai, India",
                        "average_likes": 2000,
                        "average_comments": 150,
                        "average_views": 5000,
                        "content_topics": ["Fitness", "Health", "Nutrition"]
                    }
                }
            }
        },
        404: {
            "description": "Influencer not found",
            "model": ErrorResponse
        }
    },
    tags=["influencers"]
)
async def get_influencer(influencer_id: str = Path(..., description="Unique identifier for the influencer", example="123")):
    """
    Get detailed information about a specific influencer.
    
    Returns comprehensive details including:
    - Basic profile information
    - Engagement metrics (likes, comments, views)
    - Content topics
    - Audience demographics (if available)
    - Collaboration pricing (if available)
    
    - **influencer_id**: Unique identifier for the influencer
    """
    influencer = await influencer_service.get_influencer_by_id(influencer_id)
    if not influencer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Influencer not found")
    return influencer


@router.post(
    "/analyze",
    response_model=InfluencerDetail,
    summary="Analyze New Influencer",
    description="Fetch and analyze a new influencer by their username and platform. This will retrieve data from the specified platform and add it to the database.",
    responses={
        200: {
            "description": "Influencer successfully analyzed and added",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123",
                        "username": "johndoe",
                        "display_name": "John Doe",
                        "platform": "instagram",
                        "followers": 50000,
                        "engagement_rate": 4.5,
                        "category": "Fitness"
                    }
                }
            }
        },
        404: {
            "description": "Influencer not found on the specified platform",
            "model": ErrorResponse
        }
    },
    tags=["influencers"]
)
async def analyze_influencer(
    request: AnalyzeInfluencerRequest = Body(..., description="Influencer analysis request"),
):
    """
    Analyze a new influencer by username and platform.
    
    This endpoint will:
    1. Fetch influencer data from the specified platform
    2. Analyze their profile, engagement metrics, and content
    3. Add the influencer to the database
    4. Return detailed information about the influencer
    
    **Note**: This operation may take some time depending on the platform API response time.
    
    **Supported Platforms**: instagram, twitter, youtube, tiktok, linkedin
    """
    influencer = await influencer_service.analyze_influencer(request.username, request.platform)
    if not influencer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Influencer '{request.username}' not found on {request.platform}",
        )
    return influencer


@router.post(
    "/search/nlp",
    response_model=EnhancedSearchResponse,
    summary="Natural Language Search",
    description="Search for influencers using natural language queries. The AI will understand your intent and extract relevant search parameters automatically.",
    responses={
        200: {
            "description": "Search results with relevance scores",
            "content": {
                "application/json": {
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
            }
        }
    },
    tags=["influencers", "search"]
)
async def search_nlp(request: NaturalLanguageSearchRequest):
    """
    Natural language search for influencers.
    
    Accepts free-form text queries and uses AI to understand the intent
    and extract search parameters. Returns ranked influencers with relevance scores.
    
    **How it works:**
    1. Your natural language query is analyzed by an AI agent
    2. The system extracts filters (platform, followers, category, location, etc.)
    3. Performs a hybrid search combining keyword and vector similarity
    4. Returns ranked results with relevance scores
    
    **Example queries:**
    - "Find me a fitness micro-influencer in Mumbai who is affordable"
    - "I need Gen-Z fashion creators with high engagement"
    - "Show me tech influencers with over 100K followers"
    - "Fashion bloggers in Delhi with good engagement rates"
    - "Affordable YouTube creators in the gaming niche"
    """
    results = await influencer_service.search_nlp(request)
    return results


@router.post(
    "/search/hybrid",
    response_model=EnhancedSearchResponse,
    summary="Hybrid Search",
    description="Advanced hybrid search combining keyword search, vector similarity search, and explicit filters for precise influencer discovery.",
    responses={
        200: {
            "description": "Search results from hybrid search",
            "content": {
                "application/json": {
                    "example": {
                        "influencers": [
                            {
                                "id": "123",
                                "username": "johndoe",
                                "relevance_score": 0.92
                            }
                        ],
                        "total": 30,
                        "limit": 10,
                        "offset": 0,
                        "has_more": True,
                        "search_time_ms": 180.3
                    }
                }
            }
        }
    },
    tags=["influencers", "search"]
)
async def search_hybrid(request: HybridSearchRequest):
    """
    Advanced hybrid search combining keyword, vector, and filter search.
    
    This endpoint provides maximum flexibility for influencer discovery by combining
    multiple search techniques:
    
    **Search Methods:**
    - **Keyword search**: Text-based search query for semantic matching
    - **Vector similarity**: Provide your own embedding vector for similarity search
    - **Explicit filters**: Direct filters for platform, city, followers, engagement, etc.
    
    **Use Cases:**
    - Find influencers similar to a reference influencer (use vector_query)
    - Combine semantic search with specific filters (use query + filters)
    - Fine-tune search with exact criteria (use filters only)
    
    **Note**: You can use any combination of query, vector_query, and filters.
    The system will intelligently combine them using Reciprocal Rank Fusion (RRF).
    """
    results = await influencer_service.search_hybrid(request)
    return results


@router.post(
    "/search/chat",
    response_model=ChatSearchResponse,
    summary="Conversational Search",
    description="Chat-like interface for searching influencers with natural conversation flow and refinement support. Perfect for iteratively refining your search.",
    responses={
        200: {
            "description": "Search results with conversation context",
            "content": {
                "application/json": {
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
                        "suggestions": [
                            "Filter by engagement rate",
                            "Show only verified influencers",
                            "Limit to specific platforms"
                        ]
                    }
                }
            }
        }
    },
    tags=["influencers", "search", "chat"]
)
async def search_chat(request: ChatSearchRequest):
    """
    Conversational search with refinement support - Chat-like interface.
    
    This endpoint allows users to have a natural conversation to refine their search results.
    You can start with a query and then make follow-up refinements in a conversational manner.
    
    **How it works:**
    1. Start with an initial query
    2. Review the results
    3. Make refinements using natural language
    4. The system maintains context and intelligently merges filters
    
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
        "previous_filters": { "city": "Mumbai", "interest_categories": ["Fitness"] },
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
    - "Remove the location filter" → Removes city filter
    - "Show me cheaper options" → Adjusts max_ppc downward
    
    The system maintains conversation context and intelligently merges new filters with previous ones.
    You'll receive a conversation_id to maintain context across requests.
    """
    results = await influencer_service.search_chat(request)
    return results


class ScrapeBrandRequest(BaseModel):
    """Request model for scraping brand influencers."""
    username: str = Field(..., description="Brand Instagram username", example="mamaearth")
    max_posts: int = Field(..., ge=1, le=10000, description="Maximum number of posts to scrape", example=100)
    max_api_calls: int = Field(20, ge=1, le=1000, description="Maximum API calls per brand", example=20)
    max_id: Optional[str] = Field(None, description="Last cursor/end_cursor from previous scrape to resume from a specific point")
    exclude_usernames: List[str] = Field(default_factory=list, description="List of usernames to exclude from the final influencer list")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "mamaearth",
                "max_posts": 100,
                "max_api_calls": 20,
                "max_id": None,
                "exclude_usernames": []
            }
        }


class BrandDataResponse(BaseModel):
    """Brand data response model."""
    username: str
    full_name: Optional[str] = None
    user_id: Optional[str] = None
    is_verified: Optional[bool] = None


class ScrapeBrandResponse(BaseModel):
    """Response model for brand scraping."""
    file_path: str = Field(..., description="Path to the generated Excel file")
    brand_data: BrandDataResponse = Field(..., description="Brand information")
    influencer_count: int = Field(..., description="Number of influencers found")
    last_cursor: Optional[str] = Field(None, description="Last end_cursor from this scrape. Use this as max_id in next request to resume.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "scraped_data/brand_scrape_mamaearth_2026-01-23T10-30-45.xlsx",
                "brand_data": {
                    "username": "mamaearth",
                    "full_name": "Mamaearth",
                    "user_id": "123456789",
                    "is_verified": True
                },
                "influencer_count": 25,
                "last_cursor": "QVFBS..."
            }
        }


@router.post(
    "/scrape",
    response_model=ScrapeBrandResponse,
    summary="Scrape Brand and Influencer Data",
    description="Scrape Instagram posts from a brand account and extract influencer data from collaborations.",
    responses={
        200: {
            "description": "Successfully scraped brand and influencer data",
            "content": {
                "application/json": {
                    "example": {
                        "file_path": "scraped_data/brand_scrape_mamaearth_2026-01-23T10-30-45.xlsx",
                        "brand_data": {
                            "username": "mamaearth",
                            "full_name": "Mamaearth",
                            "user_id": "123456789",
                            "is_verified": True
                        },
                        "influencer_count": 25,
                        "last_cursor": "QVFBS..."
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid parameters or no posts found",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["influencers", "scraping"]
)
async def scrape_brand(
    request: ScrapeBrandRequest = Body(..., description="Brand scraping request"),
):
    """
    Scrape brand posts and extract influencer data from Instagram.
    
    This endpoint will:
    1. Fetch Instagram posts from the specified brand account
    2. Extract brand information from the posts
    3. Identify influencers who collaborated with the brand (coauthors, tagged users)
    4. Generate an Excel file with brand and influencer data
    5. Return the file path and summary information
    
    **Features:**
    - Automatic pagination support (use `max_id` to resume from a specific point)
    - Duplicate detection (prevents same influencer from appearing multiple times)
    - Brand filtering (automatically excludes brand accounts and similar usernames)
    - Custom exclusion list (exclude specific usernames)
    - Retry logic with exponential backoff for API reliability
    
    **Parameters:**
    - **username**: Brand Instagram username (without @)
    - **max_posts**: Maximum number of posts to scrape (1-10000)
    - **max_api_calls**: Maximum API calls to make (1-1000, default: 20)
    - **max_id**: Optional cursor from previous scrape to resume pagination
    - **exclude_usernames**: List of usernames to exclude from results
    
    **Resume Scraping:**
    Use the `last_cursor` from the response as `max_id` in the next request to continue scraping
    from where you left off. This is useful for scraping large accounts in batches.
    
    **Example Request:**
    ```json
    {
        "username": "mamaearth",
        "max_posts": 100,
        "max_api_calls": 20,
        "exclude_usernames": ["competitor1", "competitor2"]
    }
    ```
    
    **Example Resume Request:**
    ```json
    {
        "username": "mamaearth",
        "max_posts": 100,
        "max_api_calls": 20,
        "max_id": "QVFBS...",
        "exclude_usernames": []
    }
    ```
    
    **Note**: This operation may take some time depending on the number of posts and API rate limits.
    The API includes automatic retry logic and rate limit handling.
    """
    from app.services.brand_scraper_service import (
        fetch_brand_posts,
        extract_brand_data,
        extract_influencer_data,
        generate_excel_file,
    )
    
    try:
        # Fetch posts
        posts, last_cursor = await fetch_brand_posts(
            request.username,
            request.max_posts,
            request.max_api_calls,
            request.max_id,
        )
        
        if not posts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No posts found for the given username",
            )
        
        # Extract brand data
        brand_data = extract_brand_data(posts, request.username)
        
        # Extract influencer data
        influencer_data = extract_influencer_data(
            posts, request.username, request.exclude_usernames or []
        )
        
        # Generate Excel file
        file_path = await generate_excel_file(brand_data, influencer_data)
        
        return ScrapeBrandResponse(
            file_path=file_path,
            brand_data=BrandDataResponse(
                username=brand_data.username,
                full_name=brand_data.full_name,
                user_id=brand_data.user_id,
                is_verified=brand_data.is_verified,
            ),
            influencer_count=len(influencer_data),
            last_cursor=last_cursor,
        )
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error scraping brand data: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape brand data: {str(error)}",
        )


async def fetch_influencer_posts(
    username: str,
    max_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch influencer posts from Instagram API.
    
    Args:
        username: Instagram username
        max_id: Optional pagination cursor
        
    Returns:
        Dictionary containing the API response data
    """
    import aiohttp
    from app.services.brand_scraper_service import make_api_call_with_retry
    
    # Clean username - remove @ if present and whitespace
    username = username.strip().lstrip("@")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty",
        )
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Fetching influencer posts for username: '{username}', max_id: '{max_id or ''}'")
            
            # Use the retry logic from brand scraper service
            response = await make_api_call_with_retry(
                session, username, max_id or "", 1
            )
            
            logger.info(f"Received response status: {response.status} for username: '{username}'")
            
            try:
                if response.status != 200:
                    # Try to parse error response
                    try:
                        error_data = await response.json()
                        error_message = error_data.get("message", error_data.get("error", str(error_data)))
                    except Exception:
                        # If JSON parsing fails, read as text
                        error_message = await response.text()
                    
                    logger.error(
                        f"Instagram API error for username '{username}': "
                        f"Status {response.status}, Message: {error_message}"
                    )
                    
                    # Return more helpful error messages
                    if response.status == 404:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User '{username}' not found on Instagram. Please verify the username is correct.",
                        )
                    elif response.status == 429:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Rate limit exceeded. Please try again later.",
                        )
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Instagram API error ({response.status}): {error_message}",
                        )
                
                # Parse successful response
                try:
                    data = await response.json()
                    return data
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON response: {json_error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Invalid response from Instagram API: {str(json_error)}",
                    )
            finally:
                response.close()
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Error fetching influencer posts for '{username}': {error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch influencer posts: {str(error)}",
            )


@router.get(
    "/fetch-details",
    summary="Fetch Influencer Details",
    description="Fetch Instagram posts and details for a specific influencer username.",
    responses={
        200: {
            "description": "Successfully fetched influencer details",
            "content": {
                "application/json": {
                    "example": {
                        "result": {
                            "edges": [
                                {
                                    "node": {
                                        "code": "ABC123",
                                        "pk": "123456789",
                                        "user": {
                                            "username": "keke",
                                            "full_name": "Keke",
                                            "pk": "123456789",
                                            "is_verified": False
                                        },
                                        "like_count": 1000,
                                        "comment_count": 50
                                    }
                                }
                            ],
                            "page_info": {
                                "has_next_page": True,
                                "end_cursor": "QVFBS..."
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid parameters",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["influencers"]
)
async def get_influencer_details(
    username: str = Query(..., description="Instagram username (without @)", example="keke"),
    max_id: Optional[str] = Query(None, description="Pagination cursor from previous request", example="QVFBS..."),
):
    """
    Fetch influencer details and posts from Instagram.
    
    This endpoint fetches posts and profile information for a specific Instagram username.
    It uses the Instagram API to retrieve the latest posts and associated metadata.
    
    **Parameters:**
    - **username**: Instagram username (without @ symbol)
    - **max_id**: Optional pagination cursor to fetch next page of results
    
    **Response:**
    Returns the raw Instagram API response containing:
    - Posts data (edges array with post nodes)
    - User information
    - Pagination info (has_next_page, end_cursor)
    - Engagement metrics (likes, comments, views)
    
    **Pagination:**
    Use the `end_cursor` from the response as `max_id` in the next request to fetch more posts.
    
    **Example Request:**
    ```
    GET /api/v1/influencers/fetch-details?username=keke
    ```
    
    **Example Request with Pagination:**
    ```
    GET /api/v1/influencers/fetch-details?username=keke&max_id=QVFBS...
    ```
    
    **Note**: This endpoint requires a valid RAPIDAPI_KEY to be configured.
    """
    try:
        data = await fetch_influencer_posts(username, max_id)
        return data
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error in get_influencer_details: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch influencer details: {str(error)}",
        )
