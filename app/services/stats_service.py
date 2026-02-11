"""Stats service for aggregating platform statistics."""
from typing import Dict, Any
from datetime import datetime, timezone

from app.services.free_influencer_service import FreeInfluencerService
from app.services.brand_service import BrandService
from app.services.brand_collaboration_service import BrandCollaborationService


class StatsService:
    """Service layer for aggregated platform statistics."""

    def __init__(self):
        self.free_influencer_service = FreeInfluencerService()
        self.brand_service = BrandService()
        self.brand_collab_service = BrandCollaborationService()

    async def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics for the platform.

        Returns:
            Dictionary with counts for free influencers, brands, and collaborations.
            Individual fields may be null if that specific count fails.
        """
        result = {
            "total_free_influencers": None,
            "total_brands": None,
            "total_brand_collaborations": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result.update(await self.free_influencer_service.get_stats())
        except Exception:
            pass

        try:
            result.update(await self.brand_service.get_stats())
        except Exception:
            pass

        try:
            result.update(await self.brand_collab_service.get_stats())
        except Exception:
            pass

        return result
