"""Brand service for business logic."""
from typing import List, Optional, Dict, Any, Tuple

from app.repositories.brand_repository import BrandRepository


class BrandService:
    """Service layer for brand operations."""

    def __init__(self):
        self.repository = BrandRepository()

    async def list_brands(
        self,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """List all brands with cursor-based pagination."""
        return await self.repository.list_all(limit=limit, cursor=cursor)

    async def create_brand(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand."""
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
