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
    id: str
    username: str
    display_name: str
    platform: Platform
    followers: int
    following: Optional[int] = None
    posts: Optional[int] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    verified: bool = False
    category: Optional[str] = None
    engagement_rate: Optional[float] = None
    location: Optional[str] = None
    average_views: Optional[int] = Field(None, description="Average views per post")
    profile_url: Optional[str] = Field(None, description="Profile URL/link")


class InfluencerDetail(Influencer):
    """Detailed influencer information."""
    average_likes: Optional[int] = None
    average_comments: Optional[int] = None
    average_views: Optional[int] = None
    recent_posts: Optional[List[dict]] = None
    audience_demographics: Optional[dict] = None
    content_topics: Optional[List[str]] = None
    collaboration_price_range: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


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
    influencers: List[Influencer]
    total: int
    limit: int
    offset: int
    has_more: bool
    relevance_scores: Optional[List[float]] = Field(None, description="Relevance scores for each influencer")
