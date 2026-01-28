"""Influencer data models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """Social media platforms."""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    
    @classmethod
    def from_string(cls, value: str):
        """Convert string to Platform enum."""
        value_lower = value.lower()
        for platform in cls:
            if platform.value == value_lower:
                return platform
        return cls.INSTAGRAM  # Default


class Influencer(BaseModel):
    """Basic influencer information."""
    id: str = Field(..., description="Unique identifier for the influencer", example="123")
    username: str = Field(..., description="Username/handle on the platform", example="johndoe")
    display_name: str = Field(..., description="Display name of the influencer", example="John Doe")
    platform: Platform = Field(..., description="Social media platform", example=Platform.INSTAGRAM)
    followers: int = Field(..., description="Number of followers", example=50000)
    following: Optional[int] = Field(None, description="Number of accounts following", example=1000)
    posts: Optional[int] = Field(None, description="Total number of posts", example=500)
    profile_image_url: Optional[str] = Field(None, description="URL to profile image", example="https://example.com/image.jpg")
    bio: Optional[str] = Field(None, description="Profile bio/description", example="Fitness enthusiast | Personal trainer")
    verified: bool = Field(False, description="Whether the account is verified", example=False)
    category: Optional[str] = Field(None, description="Primary category/niche", example="Fitness")
    engagement_rate: Optional[float] = Field(None, description="Engagement rate percentage", example=4.5)
    location: Optional[str] = Field(None, description="Location/city", example="Mumbai, India")
    average_views: Optional[int] = Field(None, description="Average views per post", example=5000)
    profile_url: Optional[str] = Field(None, description="Profile URL/link", example="https://instagram.com/johndoe")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123",
                "username": "johndoe",
                "display_name": "John Doe",
                "platform": "instagram",
                "followers": 50000,
                "following": 1000,
                "posts": 500,
                "profile_image_url": "https://example.com/image.jpg",
                "bio": "Fitness enthusiast | Personal trainer",
                "verified": False,
                "category": "Fitness",
                "engagement_rate": 4.5,
                "location": "Mumbai, India",
                "average_views": 5000,
                "profile_url": "https://instagram.com/johndoe"
            }
        }


class InfluencerDetail(Influencer):
    """Detailed influencer information."""
    average_likes: Optional[int] = Field(None, description="Average likes per post", example=2000)
    average_comments: Optional[int] = Field(None, description="Average comments per post", example=150)
    average_views: Optional[int] = Field(None, description="Average views per post/video", example=5000)
    recent_posts: Optional[List[dict]] = Field(None, description="Recent posts data", example=[{"id": "post1", "likes": 2000, "comments": 150}])
    audience_demographics: Optional[dict] = Field(None, description="Audience demographic data", example={"age_range": "18-34", "gender": {"male": 45, "female": 55}})
    content_topics: Optional[List[str]] = Field(None, description="Main content topics/themes", example=["Fitness", "Health", "Nutrition"])
    collaboration_price_range: Optional[dict] = Field(None, description="Pricing information for collaborations", example={"min": 5000, "max": 15000, "currency": "USD"})
    created_at: Optional[datetime] = Field(None, description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Record last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123",
                "username": "johndoe",
                "display_name": "John Doe",
                "platform": "instagram",
                "followers": 50000,
                "following": 1000,
                "posts": 500,
                "profile_image_url": "https://example.com/image.jpg",
                "bio": "Fitness enthusiast | Personal trainer",
                "verified": False,
                "category": "Fitness",
                "engagement_rate": 4.5,
                "location": "Mumbai, India",
                "average_views": 5000,
                "profile_url": "https://instagram.com/johndoe",
                "average_likes": 2000,
                "average_comments": 150,
                "content_topics": ["Fitness", "Health", "Nutrition"],
                "collaboration_price_range": {"min": 5000, "max": 15000, "currency": "USD"}
            }
        }


class InfluencerSearchRequest(BaseModel):
    """Request model for influencer search."""
    query: Optional[str] = None
    platform: Optional[str] = None
    min_followers: Optional[int] = Field(None, ge=0)
    max_followers: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class InfluencerSearchResponse(BaseModel):
    """Response model for influencer search."""
    influencers: List[Influencer] = Field(..., description="List of influencer results")
    total: int = Field(..., description="Total number of matching influencers", example=100)
    limit: int = Field(..., description="Number of results per page", example=10)
    offset: int = Field(..., description="Pagination offset", example=0)
    has_more: bool = Field(..., description="Whether there are more results available", example=True)
    relevance_scores: Optional[List[float]] = Field(None, description="Relevance scores for each influencer (0-1)", example=[0.95, 0.88, 0.82])
    
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
                        "category": "Fitness",
                        "engagement_rate": 4.5
                    }
                ],
                "total": 100,
                "limit": 10,
                "offset": 0,
                "has_more": True,
                "relevance_scores": [0.95, 0.88, 0.82]
            }
        }
