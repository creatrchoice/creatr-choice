"""Azure Cosmos DB client and connection management."""
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from app.core.config import settings
import asyncio


class CosmosDBClient:
    """Azure Cosmos DB client wrapper."""
    
    def __init__(self):
        """Initialize Cosmos DB client."""
        self.client: Optional[CosmosClient] = None
        self.async_client: Optional[AsyncCosmosClient] = None
        self.database = None
        self.container = None
        self.async_database = None
        self.async_container = None
    
    def connect(self) -> None:
        """Connect to Cosmos DB (synchronous)."""
        if not settings.AZURE_COSMOS_ENDPOINT or not settings.AZURE_COSMOS_KEY:
            raise ValueError("Azure Cosmos DB credentials not configured")
        
        self.client = CosmosClient(
            settings.AZURE_COSMOS_ENDPOINT,
            settings.AZURE_COSMOS_KEY
        )
        self.database = self.client.get_database_client(settings.AZURE_COSMOS_DATABASE)
        self.container = self.database.get_container_client(settings.AZURE_COSMOS_CONTAINER)
    
    async def connect_async(self) -> None:
        """Connect to Cosmos DB (asynchronous)."""
        if not settings.AZURE_COSMOS_ENDPOINT or not settings.AZURE_COSMOS_KEY:
            raise ValueError("Azure Cosmos DB credentials not configured")
        
        self.async_client = AsyncCosmosClient(
            settings.AZURE_COSMOS_ENDPOINT,
            settings.AZURE_COSMOS_KEY
        )
        # Store database and container clients
        self.async_database = self.async_client.get_database_client(settings.AZURE_COSMOS_DATABASE)
        self.async_container = self.async_database.get_container_client(settings.AZURE_COSMOS_CONTAINER)
    
    def create_database_and_container_if_not_exists(self) -> None:
        """Create database and container if they don't exist."""
        if not self.client:
            self.connect()
        
        try:
            # Create database if it doesn't exist
            self.client.create_database_if_not_exists(
                id=settings.AZURE_COSMOS_DATABASE
            )
            
            # Create container if it doesn't exist
            # Try with throughput first (for provisioned accounts)
            try:
                self.client.get_database_client(settings.AZURE_COSMOS_DATABASE).create_container_if_not_exists(
                    id=settings.AZURE_COSMOS_CONTAINER,
                    partition_key=PartitionKey(path="/platform"),
                    offer_throughput=400
                )
            except exceptions.CosmosHttpResponseError as e:
                if "serverless" in str(e).lower() or e.status_code == 400:
                    # Serverless account - create without throughput
                    self.client.get_database_client(settings.AZURE_COSMOS_DATABASE).create_container_if_not_exists(
                        id=settings.AZURE_COSMOS_CONTAINER,
                        partition_key=PartitionKey(path="/platform")
                    )
                else:
                    raise
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code != 409:  # 409 = already exists
                raise
    
    def bulk_create_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk create items in Cosmos DB.
        
        Args:
            items: List of items to create
        
        Returns:
            List of created items
        """
        if not self.container:
            self.connect()
        
        created_items = []
        for item in items:
            try:
                created_item = self.container.create_item(body=item)
                created_items.append(created_item)
            except exceptions.CosmosHttpResponseError as e:
                if e.status_code == 409:  # Conflict - item already exists
                    # Try to replace instead
                    try:
                        created_item = self.container.replace_item(
                            item=item["id"], body=item
                        )
                        created_items.append(created_item)
                    except Exception as replace_error:
                        print(f"Error replacing item {item.get('id')}: {replace_error}")
                else:
                    print(f"Error creating item {item.get('id')}: {e}")
        
        return created_items
    
    async def bulk_create_items_async(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk create items in Cosmos DB (async).
        
        Args:
            items: List of items to create
        
        Returns:
            List of created items
        """
        if not self.async_client:
            await self.connect_async()
        
        created_items = []
        tasks = []
        
        for item in items:
            task = self._create_item_async(item)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in bulk create: {result}")
            else:
                created_items.append(result)
        
        return created_items
    
    async def _create_item_async(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single item asynchronously."""
        if not self.async_container:
            await self.connect_async()
        
        try:
            created_item = await self.async_container.create_item(body=item)
            return created_item
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 409:  # Conflict
                try:
                    created_item = await self.async_container.replace_item(
                        item=item["id"], body=item
                    )
                    return created_item
                except Exception:
                    raise
            else:
                raise
    
    def query_items(self, query: str, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Query items from Cosmos DB.
        
        Args:
            query: SQL query string
            parameters: Query parameters
        
        Returns:
            List of items
        """
        if not self.container:
            self.connect()
        
        items = list(self.container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True
        ))
        return items
    
    async def query_items_async(
        self, query: str, parameters: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query items from Cosmos DB (async).
        
        Args:
            query: SQL query string
            parameters: Query parameters
        
        Returns:
            List of items
        """
        if not self.async_client:
            await self.connect_async()
        
        items = []
        # Query with cross-partition enabled (default behavior in async client)
        async for item in self.async_container.query_items(
            query=query,
            parameters=parameters or []
        ):
            items.append(item)
        
        return items
    
    def close(self) -> None:
        """Close connections."""
        if self.client:
            self.client.close()
        if self.async_client:
            # Async client cleanup would be done in async context
            pass
