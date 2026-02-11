"""Brand collaboration service for business logic."""
import hashlib
from typing import List, Optional, Dict, Any

from app.db.redis import redis_client
from app.core.config import settings
from app.repositories.brand_collaboration_repository import BrandCollaborationRepository
from app.repositories.free_influencer_repository import FreeInfluencerRepository


COSMOS_SYSTEM_FIELDS = {"_rid", "_self", "_etag", "_attachments", "_ts"}

def _generate_cache_key(brand_id: Optional[str], influencer_id: Optional[str], include_metrics: bool) -> str:
    """Generate cache key from query parameters."""
    key_parts = {
        "brand_id": brand_id or "",
        "influencer_id": influencer_id or "",
        "include_metrics": include_metrics,
    }
    key_string = hashlib.sha256(str(key_parts).encode()).hexdigest()
    return f"brand_collaborations:{key_string}"


def _clean_cosmos_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove Cosmos DB system fields from response."""
    return {k: v for k, v in data.items() if k not in COSMOS_SYSTEM_FIELDS}


class BrandCollaborationService:
    """Service layer for brand-influencer collaboration operations."""

    def __init__(self):
        self.collaboration_repo = BrandCollaborationRepository()
        self.influencer_repo = FreeInfluencerRepository()

    async def _get_cached_data(self, cache_key: str):
        """Get data from Redis cache. Returns (data, was_cached)."""
        try:
            cached = redis_client.get(cache_key)
            if cached:
                cached_list = eval(cached)
                if isinstance(cached_list, list):
                    return cached_list, True
        except Exception:
            pass
        return None, False

    async def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in Redis cache."""
        try:
            redis_client.setex(
                cache_key,
                settings.BRAND_COLLAB_CACHE_TTL,
                str(data)
            )
        except Exception:
            pass

    async def _invalidate_cache(self, pattern: str = "brand_collaborations:*") -> None:
        """Invalidate cache matching pattern."""
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception:
            pass

    async def create_collaboration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaboration with auto-generated ID."""
        if "id" not in data:
            data["id"] = BrandCollaborationRepository.create_collab_id(
                data["brand_id"],
                data["influencer_id"],
            )
        result = await self.collaboration_repo.create(data)
        await self._invalidate_cache()
        return result

    async def get_collaboration_by_id(
        self, collab_id: str, brand_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get collaboration by ID."""
        return await self.collaboration_repo.get_by_id(collab_id, brand_id)

    async def get_influencers_for_brand(
        self,
        brand_id: str,
        include_metrics: bool = False,
    ):
        """Get all influencers for a brand, optionally with collaboration metrics.

        Args:
            brand_id: Brand ID
            include_metrics: If True, merge collaboration metrics into influencer objects

        Returns:
            Tuple of (List of influencers or None, was_cached)
        """
        cache_key = _generate_cache_key(brand_id, None, include_metrics)
        cached_data, was_cached = await self._get_cached_data(cache_key)
        if was_cached:
            return cached_data, True

        collaborations = await self.collaboration_repo.get_by_brand(brand_id)

        if not collaborations:
            await self._set_cache(cache_key, [])
            return [], False

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

        await self._set_cache(cache_key, result)
        return result, False

    async def get_collaborations_for_influencer(
        self, influencer_id: str
    ) -> List[Dict[str, Any]]:
        """Get all collaborations for an influencer."""
        return await self.collaboration_repo.get_by_influencer(influencer_id)

    async def get_collaboration_by_brand_and_influencer(
        self,
        brand_id: str,
        influencer_id: str,
        include_metrics: bool = False,
    ):
        """Get specific collaboration between a brand and influencer.

        Args:
            brand_id: Brand ID
            influencer_id: Influencer ID
            include_metrics: If True, merge collaboration metrics into influencer object

        Returns:
            Tuple of (Collaboration data with influencer details or None, was_cached)
        """
        cache_key = _generate_cache_key(brand_id, influencer_id, include_metrics)
        cached_data, was_cached = await self._get_cached_data(cache_key)
        if was_cached:
            return cached_data, True

        collaboration = await self.collaboration_repo.get_by_brand_and_influencer(
            brand_id, influencer_id
        )

        if not collaboration:
            return None, False

        result = collaboration
        if include_metrics:
            influencer_id_val = collaboration.get("influencer_id") or ""
            platform = collaboration.get("platform") or "instagram"
            influencer = await self.influencer_repo.get_by_id(
                influencer_id_val, platform
            )

            if influencer:
                influencer["collaboration_metrics"] = {
                    "likes": collaboration.get("likes", 0),
                    "comments": collaboration.get("comments", 0),
                    "captured_at": collaboration.get("captured_at"),
                    "post_link": collaboration.get("post_link"),
                }
                result = _clean_cosmos_response(influencer)

        return _clean_cosmos_response(collaboration)

    async def get_stats(self) -> Dict[str, int]:
        """Get statistics for brand collaborations."""
        total = await self.collaboration_repo.count()
        return {"total_brand_collaborations": total}
