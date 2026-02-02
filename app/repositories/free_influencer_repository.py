"""Free influencer repository for Cosmos DB."""
from typing import List, Optional, Dict, Any
from app.db.cosmos_db import CosmosDBClient


class FreeInfluencerRepository:
    """Repository for free influencer data access."""
    
    def __init__(self):
        self.client = CosmosDBClient()

    async def _get_container(self):
        """Get async container client."""
        return await self.client.get_async_container_client("free_influencers")

    async def get_by_id(self, influencer_id: str, platform: str = "instagram"):
        """Get influencer by ID and platform."""
        container = await self._get_container()
        # For free_influencers, partition key is '/id'
        query = "SELECT * FROM c WHERE c.id = @id AND c.platform = @platform"
        params = [
            {"name": "@id", "value": influencer_id},
            {"name": "@platform", "value": platform},
        ]
        items = [item async for item in container.query_items(
            query=query,
            parameters=params
        )]
        return items[0] if items else None

    async def get_by_username(self, username: str, platform: str = "instagram"):
        """Get influencer by username and platform."""
        container = await self._get_container()
        query = "SELECT * FROM c WHERE c.username = @username AND c.platform = @platform"
        params = [
            {"name": "@username", "value": username},
            {"name": "@platform", "value": platform},
        ]
        items = [item async for item in container.query_items(
            query=query,
            parameters=params
        )]
        return items[0] if items else None

    async def get_by_platform(self, platform: str = "instagram", limit: int = 100):
        """Get all influencers for a platform."""
        container = await self._get_container()
        query = f"SELECT TOP {limit} * FROM c WHERE c.platform = @platform"
        params = [{"name": "@platform", "value": platform}]
        return await container.query_items(query, params)

    async def search_by_categories(self, categories: List[str]):
        """Search influencers by categories."""
        if not categories:
            return []
        
        container = await self._get_container()
        category_conditions = []
        params = []
        for i, cat in enumerate(categories):
            category_conditions.append(f"EXISTS(SELECT VALUE cat FROM cat IN c.categories WHERE cat = @cat_{i})")
            params.append({"name": f"@cat_{i}", "value": cat})
        
        query = f"""
        SELECT * FROM c 
        WHERE ARRAY_LENGTH(c.categories) > 0 
        AND ({' OR '.join(category_conditions)})
        """
        return await container.query_items(query, params)

    async def get_many_by_ids(self, influencer_ids: List[str], platform: str = "instagram"):
        """Get multiple influencers by their IDs."""
        if not influencer_ids:
            return []
            
        container = await self._get_container()
        id_conditions = []
        params = [{"name": "@platform", "value": platform}]
        
        for i, influencer_id in enumerate(influencer_ids):
            id_conditions.append(f"c.id = @id_{i}")
            params.append({"name": f"@id_{i}", "value": influencer_id})
        
        query = f"""
        SELECT * FROM c 
        WHERE c.platform = @platform 
        AND ({' OR '.join(id_conditions)})
        """
        
        return await container.query_items(query, params)

    async def create(self, influencer_data: Dict[str, Any]):
        """Create a new influencer."""
        container = await self._get_container()
        return await container.create_item(influencer_data)

    async def update(self, influencer_id: str, platform: str, influencer_data: Dict[str, Any]):
        """Update an existing influencer."""
        container = await self._get_container()
        return await container.upsert_item(influencer_id, platform, influencer_data)

    async def delete(self, influencer_id: str, platform: str = "instagram"):
        """Delete an influencer by ID and platform."""
        container = await self._get_container()
        # For free_influencers, partition key is '/id', not '/platform'
        return await container.delete_item(item=influencer_id, partition_key=influencer_id)

    async def query(self, query: str, params: List[Dict[str, Any]]):
        """Execute a custom query."""
        container = await self._get_container()
        return await container.query_items(query, params)