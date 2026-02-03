"""Brand collaboration service for business logic."""
from typing import List, Optional, Dict, Any

from app.repositories.brand_collaboration_repository import BrandCollaborationRepository
from app.repositories.free_influencer_repository import FreeInfluencerRepository


class BrandCollaborationService:
    """Service layer for brand-influencer collaboration operations."""

    def __init__(self):
        self.collaboration_repo = BrandCollaborationRepository()
        self.influencer_repo = FreeInfluencerRepository()

    async def create_collaboration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaboration with auto-generated ID."""
        if "id" not in data:
            data["id"] = BrandCollaborationRepository.create_collab_id(
                data["brand_id"],
                data["influencer_id"],
            )
        return await self.collaboration_repo.create(data)

    async def get_collaboration_by_id(
        self, collab_id: str, brand_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get collaboration by ID."""
        return await self.collaboration_repo.get_by_id(collab_id, brand_id)

    async def get_influencers_for_brand(
        self,
        brand_id: str,
        include_metrics: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get all influencers for a brand, optionally with collaboration metrics.

        Args:
            brand_id: Brand ID
            include_metrics: If True, merge collaboration metrics into influencer objects

        Returns:
            List of influencers (optionally with collaboration_metrics field)
        """
        collaborations = await self.collaboration_repo.get_by_brand(brand_id)

        if not collaborations:
            return []

        result = []
        for collab in collaborations:
            influencer_id: Optional[str] = collab.get("influencer_id")
            if not influencer_id:
                continue

            platform = collab.get("platform")
            influencer = await self.influencer_repo.get_by_id(influencer_id, platform or "instagram")

            if not influencer:
                continue

            if include_metrics:
                influencer["collaboration_metrics"] = {
                    "likes": collab.get("likes", 0),
                    "comments": collab.get("comments", 0),
                    "captured_at": collab.get("captured_at"),
                    "post_link": collab.get("post_link"),
                }

            result.append(influencer)

        return result

    async def get_collaborations_for_influencer(
        self, influencer_id: str
    ) -> List[Dict[str, Any]]:
        """Get all collaborations for an influencer."""
        return await self.collaboration_repo.get_by_influencer(influencer_id)
