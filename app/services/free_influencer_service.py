"""Free influencer service for business logic."""
from typing import List, Optional, Dict, Any, Tuple

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
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """List influencers with optional filters and pagination."""
        if platform:
            return await self.repository.get_by_platform(
                platform=platform,
                limit=limit,
                offset=offset,
            )
        if categories:
            return await self.repository.search_by_categories(
                categories=categories,
                limit=limit,
                offset=offset,
            )
        return await self.repository.get_by_platform(
            platform="instagram",
            limit=limit,
            offset=offset,
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

    async def update_influencer(
        self, influencer_id: str, data: Dict[str, Any], platform: str = "instagram"
    ) -> Dict[str, Any]:
        """Update an existing influencer (partial update)."""
        existing = await self.repository.get_by_id(influencer_id, platform)
        if not existing:
            raise ValueError(f"Influencer '{influencer_id}' not found")

        for key, value in data.items():
            if value is not None:
                existing[key] = value

        return await self.repository.update(influencer_id, platform, existing)

    async def get_stats(self) -> Dict[str, int]:
        """Get statistics for free influencers."""
        total = await self.repository.count()
        return {"total_free_influencers": total}
