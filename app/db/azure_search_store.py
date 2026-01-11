"""Azure AI Search vector store implementation."""
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings


class AzureSearchStore:
    """Azure AI Search vector store."""
    
    def __init__(self):
        """Initialize Azure AI Search client."""
        self.client: Optional[SearchClient] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize search client."""
        if not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY:
            return  # Client will be None if not configured
        
        credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        self.client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX_NAME,
            credential=credential
        )
    
    def upsert_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Upsert documents to Azure AI Search.
        
        Args:
            documents: List of documents to upsert
        """
        if not self.client:
            raise RuntimeError("Azure AI Search not configured")
        
        self.client.upload_documents(documents=documents)
    
    def search(
        self,
        query: Optional[str] = None,
        vector_query: Optional[List[float]] = None,
        filters: Optional[str] = None,
        top: int = 10,
        select: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (keyword + vector).
        
        Args:
            query: Keyword search query
            vector_query: Vector embedding for similarity search
            filters: OData filter expression
            top: Number of results to return
            select: Fields to return
        
        Returns:
            List of search results
        """
        if not self.client:
            raise RuntimeError("Azure AI Search not configured")
        
        search_options = {
            "top": top,
        }
        
        if select:
            search_options["select"] = select
        
        if filters:
            search_options["filter"] = filters
        
        # Build search queries
        search_queries = []
        
        # Keyword search
        if query:
            search_queries.append(query)
        
        # Vector search
        if vector_query:
            vectorized_query = VectorizedQuery(
                vector=vector_query,
                k_nearest_neighbors=top,
                fields="embedding"
            )
            search_options["vector_queries"] = [vectorized_query]
        
        # Perform search
        results = self.client.search(
            search_text=query or "*",
            **search_options
        )
        
        return [result for result in results]
    
    def hybrid_search(
        self,
        query: Optional[str] = None,
        vector_query: Optional[List[float]] = None,
        filters: Optional[Dict[str, Any]] = None,
        top: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search with filters.
        
        Args:
            query: Keyword search query
            vector_query: Vector embedding
            filters: Dictionary of filter conditions
            top: Number of results
        
        Returns:
            List of search results with scores
        """
        # Build OData filter string
        filter_parts = []
        
        if filters:
            if "platform" in filters and filters["platform"]:
                filter_parts.append(f"platform eq '{filters['platform']}'")
            
            if "city" in filters and filters["city"]:
                filter_parts.append(f"city eq '{filters['city']}'")
            
            if "creator_type" in filters and filters["creator_type"]:
                filter_parts.append(f"creator_type eq '{filters['creator_type']}'")
            
            if "min_followers" in filters and filters["min_followers"]:
                filter_parts.append(f"followers_count ge {filters['min_followers']}")
            
            if "max_followers" in filters and filters["max_followers"]:
                filter_parts.append(f"followers_count le {filters['max_followers']}")
            
            if "min_engagement_rate" in filters and filters["min_engagement_rate"]:
                filter_parts.append(f"engagement_rate_value ge {filters['min_engagement_rate']}")
            
            if "max_engagement_rate" in filters and filters["max_engagement_rate"]:
                filter_parts.append(f"engagement_rate_value le {filters['max_engagement_rate']}")
            
            if "min_avg_views" in filters and filters["min_avg_views"]:
                filter_parts.append(f"avg_views_count ge {filters['min_avg_views']}")
            
            if "max_avg_views" in filters and filters["max_avg_views"]:
                filter_parts.append(f"avg_views_count le {filters['max_avg_views']}")
            
            if "interest_categories" in filters and filters["interest_categories"]:
                categories = filters["interest_categories"]
                if isinstance(categories, list) and categories:
                    category_filters = " or ".join([f"interest_categories/any(c: c eq '{cat}')" for cat in categories])
                    filter_parts.append(f"({category_filters})")
            
            if "primary_category" in filters and filters["primary_category"]:
                filter_parts.append(f"primary_category eq '{filters['primary_category']}'")
        
        filter_string = " and ".join(filter_parts) if filter_parts else None
        
        return self.search(
            query=query,
            vector_query=vector_query,
            filters=filter_string,
            top=top
        )
