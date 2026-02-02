"""Free influencer service for business logic."""
from typing import List, Optional, Dict, Any

from app.repositories.free_influencer_repository import FreeInfluencerRepository


class FreeInfluencerService:
    """Service layer for free_influencer operations."""

    def __init__(self):
        self.repository = FreeInfluencerRepository()

    async def list_influencers(
        self,
        platform: Optional[str] = None,
        categories: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List influencers with optional filters."""
        if platform:
            return await self.repository.get_by_platform(
                platform=platform,
                limit=1000,
            )
        if categories:
            return await self.repository.search_by_categories(
                categories=categories,
            )
        return await self.repository.get_by_platform(
            platform="instagram",
            limit=1000,
        )

    async def create_influencer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new influencer."""
        return await self.repository.create(data)

    async def get_influencer_by_id(
        self, influencer_id: str, platform: str = "instagram"
    ) -> Optional[Dict[str, Any]]:
        """Get influencer by ID."""
        return await self.repository.get_by_id(influencer_id, platform)

    async def get_influencer_by_username(
        self, username: str, platform: str = "instagram"
    ) -> Optional[Dict[str, Any]]:
        """Get influencer by username."""
        return await self.repository.get_by_username(username, platform)
        
    async def delete_influencer(self, influencer_id: str, platform: str = "instagram"):
        """Delete an influencer by their ID."""
        return await self.repository.delete(influencer_id, platform)
