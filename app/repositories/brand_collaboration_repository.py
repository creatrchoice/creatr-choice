"""Brand collaboration repository for Cosmos DB."""
from typing import List, Optional, Dict, Any

from app.db.cosmos_db import CosmosDBClient
from app.core.config import settings


class BrandCollaborationRepository:
    """Repository for brand collaboration data access.

    Container: brand_collaborations
    Partition key: /brand_id (enables fast "get all influencers for brand X" queries)
    """

    def __init__(self):
        """Initialize repository."""
        self.cosmos_client = CosmosDBClient()
        self.container_name = settings.AZURE_COSMOS_BRAND_COLLABORATIONS_CONTAINER

    async def _get_container(self):
        """Get the async container client."""
        return await self.cosmos_client.get_async_container_client(self.container_name)

    @staticmethod
    def create_collab_id(brand_id: str, influencer_id: str) -> str:
        """Generate composite ID from brand_id and influencer_id."""
        return f"{brand_id}_{influencer_id}"

    async def get_by_id(self, collab_id: str, brand_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collaboration by ID.

        Args:
            collab_id: Collaboration ID (composite: brand_id_influencer_id)
            brand_id: Brand ID (required for partition key)

        Returns:
            Collaboration data or None
        """
        try:
            container = await self._get_container()
            return await container.read_item(item=collab_id, partition_key=brand_id)
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return None
            raise

    async def get_by_brand(self, brand_id: str) -> List[Dict[str, Any]]:
        """
        Get all collaborations for a brand.

        This is a same-partition query (fast).

        Args:
            brand_id: Brand ID

        Returns:
            List of collaborations
        """
        try:
            container = await self._get_container()

            query = "SELECT * FROM c WHERE c.brand_id = @brand_id"
            parameters = [{"name": "@brand_id", "value": brand_id}]

            items = []
            async for item in container.query_items(
                query=query,
                parameters=parameters,
                partition_key=brand_id
            ):
                items.append(item)

            return items
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return []
            raise

    async def get_by_influencer(self, influencer_id: str) -> List[Dict[str, Any]]:
        """
        Get all collaborations for an influencer.

        This is a cross-partition query (slower but acceptable).

        Args:
            influencer_id: Influencer ID

        Returns:
            List of collaborations
        """
        try:
            container = await self._get_container()

            query = "SELECT * FROM c WHERE c.influencer_id = @influencer_id"
            parameters = [{"name": "@influencer_id", "value": influencer_id}]

            items = []
            async for item in container.query_items(query=query, parameters=parameters):
                items.append(item)

            return items
        except Exception as e:
            if "Resource Not Found" in str(e) or "NotFound" in str(e):
                return []
            raise

    async def create(self, collaboration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new collaboration.

        Args:
            collaboration: Collaboration data (must include 'id', 'brand_id', 'influencer_id')

        Returns:
            Created collaboration
        """
        container = await self._get_container()

        if "id" not in collaboration:
            collaboration["id"] = self.create_collab_id(
                collaboration["brand_id"],
                collaboration["influencer_id"]
            )

        return await container.create_item(body=collaboration)

    async def update(self, collab_id: str, brand_id: str, collaboration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing collaboration.

        Args:
            collab_id: Collaboration ID
            brand_id: Brand ID (partition key)
            collaboration: Updated collaboration data

        Returns:
            Updated collaboration
        """
        container = await self._get_container()

        collaboration["id"] = collab_id

        return await container.replace_item(item=collab_id, partition_key=brand_id, body=collaboration)

    async def delete(self, collab_id: str, brand_id: str) -> bool:
        """
        Delete a collaboration.

        Args:
            collab_id: Collaboration ID
            brand_id: Brand ID (partition key)

        Returns:
            True if deleted
        """
        container = await self._get_container()

        await container.delete_item(item=collab_id, partition_key=brand_id)
        return True
