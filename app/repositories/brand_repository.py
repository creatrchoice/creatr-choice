"""Brand repository for Cosmos DB."""
from typing import List, Optional, Dict, Any, Tuple

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

    async def list_all(self, limit: int = 20, cursor: Optional[str] = None) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List all brands with pagination using offset from cursor.

        Args:
            limit: Maximum number of brands to return
            cursor: Offset encoded as cursor (base64 or plain number)

        Returns:
            Tuple of (list of brands, next cursor or None)
        """
        try:
            container = await self._get_container()

            # Decode cursor to offset (cursor is just the offset number as string)
            offset = 0
            if cursor:
                try:
                    offset = int(cursor)
                except (ValueError, TypeError):
                    offset = 0

            query = "SELECT * FROM c ORDER BY c.created_at ASC OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]

            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters
            ):
                items.append(item)

            # Generate next cursor if we got a full page
            next_cursor = None
            if len(items) == limit:
                next_cursor = str(offset + limit)

            return items, next_cursor
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return [], None
            raise

    async def count(self) -> int:
        """Get total count of brands."""
        container = await self._get_container()
        query = "SELECT VALUE COUNT(1) FROM c"
        items = [item async for item in container.query_items(query=query)]
        return items[0] if items else 0
