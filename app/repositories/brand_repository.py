"""Brand repository for Cosmos DB."""
from typing import List, Optional, Dict, Any

from app.db.cosmos_db import CosmosDBClient
from app.core.config import settings


class BrandRepository:
    """Repository for brand data access.

    Container: brands
    Partition key: /id
    """

    def __init__(self):
        """Initialize repository."""
        self.cosmos_client = CosmosDBClient()
        self.container_name = settings.AZURE_COSMOS_BRANDS_CONTAINER

    async def _get_container(self):
        """Get the async container client."""
        return await self.cosmos_client.get_async_container_client(self.container_name)

    async def get_by_id(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """
        Get brand by ID.

        Args:
            brand_id: Brand ID

        Returns:
            Brand data or None
        """
        try:
            container = await self._get_container()
            return await container.read_item(item=brand_id, partition_key=brand_id)
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return None
            raise

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get brand by name.

        Args:
            name: Brand name

        Returns:
            Brand data or None
        """
        try:
            container = await self._get_container()

            query = "SELECT * FROM c WHERE c.name = @name"
            parameters = [{"name": "@name", "value": name}]

            items = []
            async for item in container.query_items(query=query, parameters=parameters):
                items.append(item)

            return items[0] if items else None
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return None
            raise

    async def create(self, brand: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new brand.

        Args:
            brand: Brand data dictionary (must include 'id')

        Returns:
            Created brand
        """
        container = await self._get_container()
        return await container.create_item(body=brand)

    async def update(self, brand_id: str, brand: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing brand.

        Args:
            brand_id: Brand ID
            brand: Updated brand data

        Returns:
            Updated brand
        """
        container = await self._get_container()

        brand["id"] = brand_id

        return await container.replace_item(item=brand_id, body=brand)

    async def delete(self, brand_id: str) -> bool:
        """
        Delete a brand.

        Args:
            brand_id: Brand ID

        Returns:
            True if deleted
        """
        container = await self._get_container()

        await container.delete_item(item=brand_id, partition_key=brand_id)
        return True

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all brands with pagination.

        Args:
            limit: Maximum number of brands to return
            offset: Number of brands to skip

        Returns:
            List of brands
        """
        try:
            container = await self._get_container()

            query = "SELECT * FROM c OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]

            items = []
            async for item in container.query_items(query=query, parameters=parameters):
                items.append(item)

            return items
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return []
            raise
