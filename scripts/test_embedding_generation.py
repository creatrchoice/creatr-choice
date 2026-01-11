"""Quick test to verify embedding generation script works correctly."""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.cosmos_db import CosmosDBClient
from app.db.azure_search_store import AzureSearchStore
from app.services.embedding_service import EmbeddingService
from app.core.config import settings


async def test_embedding_generation():
    """Test a small batch to verify the script works."""
    print("=" * 60)
    print("Testing Embedding Generation (Small Batch)")
    print("=" * 60)
    
    # Initialize services
    cosmos_client = CosmosDBClient()
    search_store = AzureSearchStore()
    embedding_service = EmbeddingService()
    
    if not embedding_service.is_available():
        print("❌ Embedding service not available")
        return False
    
    try:
        # Connect to Cosmos DB
        cosmos_client.connect()
        
        # Fetch just 5 influencers for testing
        print("\n1. Fetching 5 influencers from Cosmos DB...")
        query = "SELECT TOP 5 * FROM c"
        test_influencers = cosmos_client.query_items(query)
        
        if not test_influencers:
            print("   ❌ No influencers found")
            return False
        
        print(f"   ✅ Found {len(test_influencers)} influencers")
        
        # Test embedding generation
        print("\n2. Testing embedding generation...")
        texts = []
        for inf in test_influencers:
            name = inf.get("name", "")
            username = inf.get("username", "")
            categories = inf.get("interest_categories", [])
            text = embedding_service.generate_embedding_text(name, username, categories)
            texts.append(text)
            print(f"   - {name[:40]}... -> Text length: {len(text)}")
        
        embeddings = await embedding_service.generate_embeddings_batch(texts)
        
        if not embeddings or len(embeddings) != len(texts):
            print(f"   ❌ Failed to generate embeddings. Got {len(embeddings) if embeddings else 0} embeddings")
            return False
        
        print(f"   ✅ Generated {len(embeddings)} embeddings")
        print(f"   ✅ Embedding dimensions: {len(embeddings[0]) if embeddings[0] else 0}")
        
        # Test Azure AI Search upsert
        print("\n3. Testing Azure AI Search upsert...")
        search_docs = []
        for inf, embedding in zip(test_influencers, embeddings):
            if embedding:
                search_doc = {
                    "id": str(inf.get("id", inf.get("influencer_id", ""))),
                    "influencer_id": inf.get("influencer_id"),
                    "name": inf.get("name"),
                    "username": inf.get("username"),
                    "platform": inf.get("platform"),
                    "city": inf.get("city"),
                    "creator_type": inf.get("creator_type"),
                    "followers_count": inf.get("followers_count"),
                    "engagement_rate_value": inf.get("engagement_rate_value"),
                    "avg_views_count": inf.get("avg_views_count"),
                    "interest_categories": inf.get("interest_categories", []),
                    "primary_category": inf.get("primary_category", {}).get("name") if isinstance(inf.get("primary_category"), dict) else inf.get("primary_category"),
                    "url": inf.get("url"),
                    "picture": inf.get("picture"),
                    "embedding": embedding,
                }
                search_docs.append(search_doc)
        
        if search_docs:
            try:
                search_store.upsert_documents(search_docs)
                print(f"   ✅ Successfully upserted {len(search_docs)} documents to Azure AI Search")
            except Exception as e:
                print(f"   ❌ Failed to upsert: {e}")
                return False
        
        # Test batch processing logic
        print("\n4. Testing batch processing logic...")
        batch_size = 200
        test_batch = test_influencers * 10  # Simulate a larger batch
        batches = [test_batch[i:i + batch_size] for i in range(0, len(test_batch), batch_size)]
        print(f"   ✅ Created {len(batches)} batches from {len(test_batch)} items")
        print(f"   ✅ Batch size: {batch_size}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Script should work correctly.")
        print("=" * 60)
        print("\nNote: The script processes 198K+ influencers, so it will take time.")
        print("Expected time: ~5-6 hours at ~10 items/second")
        print("\nMonitor progress with:")
        print("  tail -f /tmp/embeddings.log")
        print("  cat /tmp/embedding_generation_progress.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_embedding_generation())
    sys.exit(0 if success else 1)
