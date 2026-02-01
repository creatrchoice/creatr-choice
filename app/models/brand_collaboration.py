"""Brand collaboration data models."""
from pydantic import BaseModel


class BrandCollaboration(BaseModel):
    """Brand collaboration model - flat metrics.

    Represents a brand-influencer partnership with engagement data.

    Partition key: /brand_id (enables fast "get all influencers for brand X" queries)
    """
    id: str  # Composite key: "{brand_id}_{influencer_id}"
    brand_id: str
    influencer_id: str
    likes: int
    comments: int
    captured_at: str

    @classmethod
    def create_id(cls, brand_id: str, influencer_id: str) -> str:
        """Generate composite ID from brand_id and influencer_id."""
        return f"{brand_id}_{influencer_id}"
