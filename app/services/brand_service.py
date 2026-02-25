"""Brand service for business logic."""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import time

from app.repositories.brand_repository import BrandRepository
from app.repositories.brand_collaboration_repository import BrandCollaborationRepository
from app.core.constants import BRAND_ROTATION_START_DATE


class BrandService:
    """Service layer for brand operations."""

    def __init__(self):
        self.repository = BrandRepository()
        self.collaboration_repository = BrandCollaborationRepository()

    async def list_brands(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """List all brands with cursor-based pagination."""
        brands, next_cursor = await self.repository.list_all(limit=limit, cursor=cursor)
        
        brand_ids = [brand["id"] for brand in brands]
        counts = await self.collaboration_repository.get_by_brand_ids(brand_ids)
        
        for idx, brand in enumerate(brands):
            brand["isAvailable"] = self._is_brand_available(idx + offset)
            brand["totalCount"] = counts.get(brand["id"], 0)
        
        return brands, next_cursor
    
    def _is_brand_available(self, index: int) -> bool:
        """Determine if a brand is available based on days since start date."""
        current_time_ms = int(time.time() * 1000)
        days_elapsed = (current_time_ms - BRAND_ROTATION_START_DATE) // (2 * 24 * 60 * 60 * 1000)
        available_count = 20 + days_elapsed
        return index < available_count

    async def create_brand(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand."""
        if "created_at" not in data or data["created_at"] is None:
            data["created_at"] = datetime.utcnow().isoformat()
        return await self.repository.create(data)

    async def get_brand_by_id(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """Get brand by ID."""
        return await self.repository.get_by_id(brand_id)

    async def get_brand_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get brand by name."""
        return await self.repository.get_by_name(name)

    async def delete_brand(self, brand_id: str) -> bool:
        """Delete a brand by ID."""
        return await self.repository.delete(brand_id)

    async def update_brand(self, brand_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing brand (partial update)."""
        existing = await self.repository.get_by_id(brand_id)
        if not existing:
            raise ValueError(f"Brand '{brand_id}' not found")

        for key, value in data.items():
            if value is not None:
                existing[key] = value

        return await self.repository.update(brand_id, existing)

    async def get_stats(self) -> Dict[str, int]:
        """Get statistics for brands."""
        total = await self.repository.count()
        return {"total_brands": total}
