"""Category metadata models."""
from pydantic import BaseModel
from typing import List, Optional


class CategoryStatistic(BaseModel):
    """Statistics for a category."""
    name: str
    count: int
    avg_engagement_rate: Optional[float] = None
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    avg_followers: Optional[float] = None


class CategoryMetadata(BaseModel):
    """Complete category metadata."""
    interest_categories: List[CategoryStatistic] = []
    primary_categories: List[CategoryStatistic] = []
    cities: List[str] = []
    creator_types: List[str] = []
    platforms: List[str] = []
    total_influencers: int = 0
