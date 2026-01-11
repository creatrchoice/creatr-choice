"""Influencer repository for Cosmos DB."""
from typing import List, Optional, Dict, Any
from app.db.cosmos_db import CosmosDBClient
from app.models.influencer_data import InfluencerData


class InfluencerRepository:
    """Repository for influencer data access."""
    
    def __init__(self):
        """Initialize repository."""
        self.cosmos_client = CosmosDBClient()
    
    async def get_by_id(self, influencer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get influencer by ID.
        
        Args:
            influencer_id: Influencer ID
        
        Returns:
            Influencer data or None
        """
        await self.cosmos_client.connect_async()
        
        query = "SELECT * FROM c WHERE c.id = @id"
        parameters = [{"name": "@id", "value": influencer_id}]
        
        results = await self.cosmos_client.query_items_async(query, parameters)
        return results[0] if results else None
    
    async def get_by_influencer_id(self, influencer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get influencer by influencer_id field.
        
        Args:
            influencer_id: Influencer ID number
        
        Returns:
            Influencer data or None
        """
        await self.cosmos_client.connect_async()
        
        query = "SELECT * FROM c WHERE c.influencer_id = @id"
        parameters = [{"name": "@id", "value": influencer_id}]
        
        results = await self.cosmos_client.query_items_async(query, parameters)
        return results[0] if results else None
    
    async def create(self, influencer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new influencer.
        
        Args:
            influencer_data: Influencer data dictionary
        
        Returns:
            Created influencer
        """
        await self.cosmos_client.connect_async()
        return await self.cosmos_client._create_item_async(influencer_data)
    
    async def bulk_create(self, influencers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk create influencers.
        
        Args:
            influencers: List of influencer data dictionaries
        
        Returns:
            List of created influencers
        """
        await self.cosmos_client.connect_async()
        return await self.cosmos_client.bulk_create_items_async(influencers)
