"""Influencer data models matching the JSON schema from MongoDB."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Interest(BaseModel):
    """Interest category model."""
    name: str


class PrimaryCategory(BaseModel):
    """Primary category model."""
    name: str


class Prediction(BaseModel):
    """Prediction model for influencer metrics."""
    followers: int
    views: int
    enagaged_users: int
    enagaged_users_display: str
    engagement_rate: float
    enagaged_users_count: int


class InfluencerData(BaseModel):
    """Complete influencer data model matching MongoDB schema."""
    id: int
    avg_views: Optional[str] = None
    avg_views_count: Optional[int] = None
    avg_views_display: Optional[str] = None
    city: Optional[str] = None
    creator_type: Optional[str] = None
    engagement_rate: Optional[str] = None
    engagement_rate_display: Optional[str] = None
    engagement_rate_value: Optional[float] = None
    engagements: Optional[int] = None
    engagements_count: Optional[int] = None
    fetched_at: Optional[datetime] = None
    fetched_page: Optional[int] = None
    followers: Optional[str] = None
    followers_count: Optional[int] = None
    followers_display: Optional[str] = None
    influencer_id: int
    interest_categories: List[str] = Field(default_factory=list)
    interests: List[Interest] = Field(default_factory=list)
    language: Optional[str] = None
    local_image_path: Optional[str] = None
    location: Optional[str] = None
    name: str
    picture: Optional[str] = None
    platform: str
    ppc: Optional[int] = None
    prediction: Optional[Prediction] = None
    primary_category: Optional[PrimaryCategory] = None
    processed_at: Optional[datetime] = None
    speed_score: Optional[int] = None
    url: Optional[str] = None
    username: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
