"""Free influencer schemas - request (validated) and response (documented only)."""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime


class CreateInfluencerRequest(BaseModel):
    """Validated request for creating an influencer."""
    id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$",
                    description="Unique identifier", example="infl_123")
    platform: str = Field(..., min_length=1, max_length=20,
                          description="Social media platform", example="instagram")
    platform_user_id: str = Field(..., min_length=1, max_length=100,
                                  description="User ID on platform", example="123456789")
    username: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_.]+$",
                          description="Username/handle", example="johndoe")
    full_name: str = Field(..., min_length=1, max_length=100,
                           description="Full name", example="John Doe")
    bio: Optional[str] = Field(None, max_length=500, description="Profile bio")
    is_private: bool = Field(False, description="Whether account is private")
    followers: int = Field(..., ge=0, description="Number of followers", example=10000)
    following: int = Field(..., ge=0, description="Number following", example=500)
    post_count: int = Field(..., ge=0, description="Number of posts", example=100)
    categories: Optional[List[str]] = Field(None, max_length=10, description="Content categories")
    location: Optional[str] = Field(None, max_length=100, description="Location")
    profile_image: Dict[str, str] = Field(..., description="Profile image URLs",
                                          example={"url": "https://...", "hd": "https://..."})
    last_fetched_at: str = Field(..., description="ISO 8601 datetime",
                                 example="2026-02-01T10:00:00Z")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        valid = ["instagram", "twitter", "youtube", "tiktok", "linkedin"]
        if v.lower() not in valid:
            raise ValueError(f"platform must be one of: {', '.join(valid)}")
        return v.lower()

    @field_validator("last_fetched_at")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("last_fetched_at must be valid ISO 8601 format")
        return v



    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "infl_123",
            "platform": "instagram",
            "platform_user_id": "123456789",
            "username": "johndoe",
            "full_name": "John Doe",
            "bio": "Fitness enthusiast",
            "is_private": False,
            "followers": 10000,
            "following": 500,
            "post_count": 100,
            "categories": ["fitness", "travel"],
            "location": "Mumbai",
            "profile_image": {"url": "https://...", "hd": "https://..."},
            "last_fetched_at": "2026-02-01T10:00:00Z"
        }
    })


class InfluencerResponse(BaseModel):
    """Response model - no validation, just documentation."""
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

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "infl_123",
            "platform": "instagram",
            "platform_user_id": "123456789",
            "username": "johndoe",
            "full_name": "John Doe",
            "bio": "Fitness enthusiast",
            "is_private": False,
            "followers": 10000,
            "following": 500,
            "post_count": 100,
            "categories": ["fitness", "travel"],
            "location": "Mumbai",
            "profile_image": {"url": "https://...", "hd": "https://..."},
            "last_fetched_at": "2026-02-01T10:00:00Z"
        }
    })


class InfluencerListResponse(BaseModel):
    """Response for list of influencers."""
    data: List[InfluencerResponse]
    count: int = Field(..., description="Number of results")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "data": [
                {"id": "infl_1", "username": "johndoe", "followers": 10000, "platform": "instagram"}
            ],
            "count": 1,
        }
    })
