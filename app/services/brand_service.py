"""Brand service for business logic."""
from typing import List, Optional, Dict, Any

from app.repositories.brand_repository import BrandRepository


class BrandService:
    """Service layer for brand operations."""

    def __init__(self):
        self.repository = BrandRepository()

    async def list_brands(
        self,
    ) -> List[Dict[str, Any]]:
        """List all brands with pagination."""
        return await self.repository.list_all()

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
