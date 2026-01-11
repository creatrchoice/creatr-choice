"""Create Azure AI Search index programmatically."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    HnswParameters,
)
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings


def create_index():
    """Create Azure AI Search index with vector search support."""
    print("=" * 60)
    print("Creating Azure AI Search Index")
    print("=" * 60)
    
    if not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY:
        print("ERROR: Azure AI Search credentials not configured in .env")
        return False
    
    try:
        # Initialize client
        credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        client = SearchIndexClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            credential=credential
        )
        
        # Define fields
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(name="influencer_id", type=SearchFieldDataType.Int64),
            SearchField(name="name", type=SearchFieldDataType.String, searchable=True),
            SearchField(name="username", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SearchField(name="platform", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(name="city", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(name="creator_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(name="followers_count", type=SearchFieldDataType.Int64, filterable=True, sortable=True),
            SearchField(name="engagement_rate_value", type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SearchField(name="avg_views_count", type=SearchFieldDataType.Int64, filterable=True, sortable=True),
            SearchField(name="interest_categories", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
            SearchField(name="primary_category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchField(name="url", type=SearchFieldDataType.String, filterable=False),
            SearchField(name="picture", type=SearchFieldDataType.String, filterable=False),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=3072,  # text-embedding-3-large produces 3072 dimensions
                vector_search_profile_name="my-vector-profile"
            ),
        ]
        
        # Define vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="my-hnsw-config",
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric="cosine"
                    )
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="my-vector-profile",
                    algorithm_configuration_name="my-hnsw-config"
                )
            ]
        )
        
        # Create index
        index = SearchIndex(
            name=settings.AZURE_SEARCH_INDEX_NAME,
            fields=fields,
            vector_search=vector_search
        )
        
        # Check if index exists
        try:
            existing_index = client.get_index(settings.AZURE_SEARCH_INDEX_NAME)
            print(f"Index '{settings.AZURE_SEARCH_INDEX_NAME}' already exists.")
            response = input("Do you want to delete and recreate it? (yes/no): ")
            if response.lower() == "yes":
                client.delete_index(settings.AZURE_SEARCH_INDEX_NAME)
                print("Deleted existing index.")
            else:
                print("Keeping existing index.")
                return True
        except Exception:
            # Index doesn't exist, proceed with creation
            pass
        
        # Create the index
        print(f"Creating index '{settings.AZURE_SEARCH_INDEX_NAME}'...")
        client.create_index(index)
        print(f"✓ Index '{settings.AZURE_SEARCH_INDEX_NAME}' created successfully!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create index: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_index()
    sys.exit(0 if success else 1)
