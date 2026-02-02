"""Brand collaboration schemas - request (validated) and response (documented only)."""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class CreateCollaborationRequest(BaseModel):
    brand_id: str = Field(..., min_length=1, max_length=100,
                          description="Brand ID", example="brand_123")
    influencer_id: str = Field(..., min_length=1, max_length=100,
                               description="Influencer ID", example="infl_456")
    likes: int = Field(0, ge=0, description="Total likes from collaboration posts")
    comments: int = Field(0, ge=0, description="Total comments from collaboration posts")
    captured_at: str = Field(..., description="ISO 8601 datetime when metrics captured",
                             example="2026-02-01T10:00:00Z")
    post_link: Optional[str] = Field(None, max_length=500, description="Instagram post URL")

    @field_validator("captured_at")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("captured_at must be valid ISO 8601 format")
        return v

    @model_validator(mode="after")
    def validate_non_negative(self):
        if self.likes < 0 or self.comments < 0:
            raise ValueError("likes and comments must be non-negative")
        return self

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "brand_id": "brand_123",
            "influencer_id": "infl_456",
            "likes": 50000,
            "comments": 1200,
            "captured_at": "2026-02-01T10:00:00Z",
            "post_link": "https://instagram.com/p/abc123"
        }
    })


class CollaborationMetrics(BaseModel):
    likes: int
    comments: int
    captured_at: str
    post_link: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {"likes": 50000, "comments": 1200, "captured_at": "2026-02-01T10:00:00Z"}
    })


class InfluencerWithMetrics(BaseModel):
    id: str
    platform: str
    platform_user_id: str
    username: str
    full_name: str
    bio: Optional[str]
    is_private: bool
    followers: int
    following: int
    post_count: int
    categories: Optional[List[str]]
    location: Optional[str]
    profile_image: Dict[str, str]
    last_fetched_at: str
    collaboration_metrics: Optional[CollaborationMetrics] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "infl_456",
            "platform": "instagram",
            "username": "johndoe",
            "full_name": "John Doe",
            "followers": 10000,
            "collaboration_metrics": {"likes": 50000, "comments": 1200}
        }
    })


class CollaborationResponse(BaseModel):
    id: str
    brand_id: str
    influencer_id: str
    likes: int
    comments: int
    captured_at: str
    post_link: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "brand_123_infl_456",
            "brand_id": "brand_123",
            "influencer_id": "infl_456",
            "likes": 50000,
            "comments": 1200,
            "captured_at": "2026-02-01T10:00:00Z",
            "post_link": "https://instagram.com/p/abc123"
        }
    })


class InfluencerListForBrandResponse(BaseModel):
    data: List[InfluencerWithMetrics]
    count: int
    brand_id: str
    include_metrics: bool

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "data": [{"id": "infl_1", "username": "johndoe", "collaboration_metrics": {"likes": 50000}}],
            "count": 1,
            "brand_id": "brand_123",
            "include_metrics": True
        }
    })


class CollaborationListForInfluencerResponse(BaseModel):
    data: List[CollaborationResponse]
    count: int
    influencer_id: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "data": [{"id": "brand_123_infl_456", "brand_id": "brand_123", "likes": 50000}],
            "count": 1,
            "influencer_id": "infl_456"
        }
    })
