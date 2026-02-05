"""Influencer data models - simplified."""
from pydantic import BaseModel
from typing import Optional, List

class ProfileImage(BaseModel):
    """Profile image URLs."""
    url: str
    hd: str

class Influencer(BaseModel):
    """Influencer model matching exact specs."""
    id: str
    platform: str
    platform_user_id: str
    username: str
    full_name: str
    bio: Optional[str] = None
    is_private: bool
    followers: int
    following: int
    post_count: int
    categories: Optional[List[str]] = None
    location: Optional[str] = None
    profile_image: ProfileImage
    last_fetched_at: str
