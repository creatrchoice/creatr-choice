"""Free influencer repository for Cosmos DB."""
from typing import List, Optional, Dict, Any

from app.db.cosmos_db import CosmosDBClient
from app.core.config import settings


class FreeInfluencerRepository:
    """Repository for free_influencer.Influencer model data access.

    Container: influencers
    Partition key: /platform
    """

    def __init__(self):
        """Initialize repository."""
        self.cosmos_client = CosmosDBClient()
        self.container_name = settings.AZURE_COSMOS_INFLUENCERS_CONTAINER

    async def _get_container(self):
        """Get the async container client."""
        return await self.cosmos_client.get_async_container_client(self.container_name)

    async def get_by_id(self, influencer_id: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get influencer by ID.

        Args:
            influencer_id: Influencer ID
            platform: Platform (optional, improves query performance if provided)

        Returns:
            Influencer data or None
        """
        container = await self._get_container()

        if platform:
            try:
                return await container.read_item(item=influencer_id, partition_key=platform)
            except Exception:
                return None

        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": influencer_id}]

        items = []
        async for item in container.query_items(query=query, parameters=parameters):
            items.append(item)

        return items[0] if items else None

    async def get_by_username(self, username: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get influencer by username.

        Args:
            username: Username
            platform: Platform (optional, improves query performance if provided)

        Returns:
            Influencer data or None
        """
        container = await self._get_container()

        query = "SELECT * FROM c WHERE c.username = @username"
        parameters = [{"name": "@username", "value": username}]

        # Add platform filter if provided (same-partition query)
        if platform:
            query += " AND c.platform = @platform"
            parameters.append({"name": "@platform", "value": platform})

        items = []
        async for item in container.query_items(query=query, parameters=parameters):
            items.append(item)

        return items[0] if items else None

    async def get_by_platform(self, platform: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all influencers for a platform.

        This is a same-partition query (fast).

        Args:
            platform: Platform name (e.g., "instagram", "youtube")
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of influencers
        """
        container = await self._get_container()

        query = "SELECT * FROM c WHERE c.platform = @platform OFFSET @offset LIMIT @limit"
        parameters = [
            {"name": "@platform", "value": platform},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]

        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=platform
        ):
            items.append(item)

        return items

    async def create(self, influencer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new influencer.

        Args:
            influencer: Influencer data (must include 'id' and 'platform')

        Returns:
            Created influencer
        """
        container = await self._get_container()
        return await container.create_item(body=influencer)

    async def update(self, influencer_id: str, platform: str, influencer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing influencer.

        Args:
            influencer_id: Influencer ID
            platform: Platform (partition key)
            influencer: Updated influencer data

        Returns:
            Updated influencer
        """
        container = await self._get_container()

        # Ensure id and platform are set
        influencer["id"] = influencer_id
        influencer["platform"] = platform

        return await container.replace_item(item=influencer_id, body=influencer)

    async def delete(self, influencer_id: str, platform: str) -> bool:
        """
        Delete an influencer.

        Args:
            influencer_id: Influencer ID
            platform: Platform (partition key)

        Returns:
            True if deleted
        """
        container = await self._get_container()

        await container.delete_item(item=influencer_id, partition_key=platform)
        return True

    async def search_by_categories(
        self,
        categories: List[str],
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search influencers by categories.

        Args:
            categories: List of categories to match
            platform: Platform filter (optional)
            limit: Maximum number of results

        Returns:
            List of matching influencers
        """
        container = await self._get_container()

        if not categories:
            return []

        # Use first category for initial filter (Cosmos DB ARRAY_CONTAINS)
        primary_category = categories[0]
        other_categories = categories[1:]

        # Build query with ARRAY_CONTAINS for server-side filtering
        query = """
            SELECT * FROM c
            WHERE ARRAY_CONTAINS(c.categories, @category)
        """
        parameters = [{"name": "@category", "value": primary_category}]

        if platform:
            query += " AND c.platform = @platform"
            parameters.append({"name": "@platform", "value": platform})

        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=platform if platform else None,
            max_item_count=limit * 2  # Fetch more to filter for additional categories
        ):
            # Filter for additional categories in Python
            if other_categories:
                item_categories = item.get("categories", []) or []
                if not any(cat in item_categories for cat in other_categories):
                    continue

            items.append(item)
            if len(items) >= limit:
                break

        return items
