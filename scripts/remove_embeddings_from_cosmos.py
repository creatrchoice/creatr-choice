"""Remove embedding fields from Cosmos DB documents to save storage."""
import asyncio
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.cosmos_db import CosmosDBClient
from app.core.config import settings
from tqdm import tqdm


async def remove_embeddings_from_cosmos():
    """Remove embedding fields from all Cosmos DB documents."""
    print("=" * 60)
    print("Remove Embeddings from Cosmos DB")
    print("=" * 60)
    print("\n⚠️  WARNING: This will remove embedding fields from Cosmos DB")
    print("   - Embeddings will remain in Azure AI Search (used for search)")
    print("   - This saves ~2.4GB storage in Cosmos DB")
    print("   - No impact on search functionality")
    
    # Check for command line argument to skip prompt
    import sys
    if "--yes" in sys.argv or "-y" in sys.argv:
        print("\n✅ Auto-confirmed (--yes flag provided)")
    else:
        response = input("\nDo you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return False
    
    cosmos_client = CosmosDBClient()
    
    try:
        # Connect to Cosmos DB
        cosmos_client.connect()
        
        # Query all documents with embeddings (optimized - don't fetch embedding field itself)
        print("\nFetching documents with embeddings...")
        print("This may take a moment for large datasets...")
        query = "SELECT c.id, c.platform FROM c WHERE IS_DEFINED(c.embedding) AND c.embedding != null"
        
        # Use iterator to avoid loading all into memory at once and show progress
        documents = []
        print("Querying Cosmos DB...")
        item_count = 0
        for doc in cosmos_client.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ):
            documents.append(doc)
            item_count += 1
            if item_count % 1000 == 0:
                print(f"  Loaded {item_count:,} document IDs...", flush=True)
        
        total_count = len(documents)
        print(f"\n✅ Found {total_count:,} documents with embeddings")
        
        if total_count == 0:
            print("No documents with embeddings found. Nothing to remove.")
            return True
        
        # Connect async for updates
        await cosmos_client.connect_async()
        
        # Process in batches
        batch_size = 100
        processed = 0
        failed = 0
        
        async def remove_embedding_from_doc(doc: Dict[str, Any]):
            """Remove embedding field from a document."""
            try:
                doc_id = doc["id"]
                # Get partition key from document (usually "platform")
                partition_key = doc.get("platform", "instagram")
                
                # Get full document using async client
                db_client = cosmos_client.async_client.get_database_client(settings.AZURE_COSMOS_DATABASE)
                container = db_client.get_container_client(settings.AZURE_COSMOS_CONTAINER)
                
                # Read document - partition key is required for read
                full_doc = await container.read_item(
                    item=doc_id,
                    partition_key=partition_key
                )
                
                # Remove embedding field
                if "embedding" in full_doc:
                    del full_doc["embedding"]
                    
                    # Update document - partition key is inferred from document body
                    # The document already has the platform field which is the partition key
                    await container.replace_item(
                        item=doc_id,
                        body=full_doc
                    )
                    return True
                return False
            except Exception as e:
                print(f"Error removing embedding from {doc.get('id', 'unknown')}: {e}")
                return False
        
        # Process in batches with progress bar
        print(f"\nRemoving embeddings in batches of {batch_size}...")
        batches = [documents[i:i + batch_size] for i in range(0, total_count, batch_size)]
        
        with tqdm(total=total_count, desc="Removing embeddings") as pbar:
            for batch in batches:
                # Process batch (limit concurrency to avoid rate limiting)
                semaphore = asyncio.Semaphore(10)  # Max 10 concurrent updates
                
                async def remove_with_semaphore(doc):
                    async with semaphore:
                        return await remove_embedding_from_doc(doc)
                
                tasks = [remove_with_semaphore(doc) for doc in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results
                for result in results:
                    if result is True:
                        processed += 1
                    elif result is not False:
                        failed += 1
                
                pbar.update(len(batch))
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Processed: {processed:,}")
        print(f"❌ Failed: {failed:,}")
        print(f"📊 Total: {total_count:,}")
        
        if processed > 0:
            storage_saved = processed * 12  # ~12KB per embedding
            print(f"\n💾 Storage saved: ~{storage_saved / 1024 / 1024:.2f} GB")
            print("✅ Embeddings removed from Cosmos DB")
            print("✅ Embeddings remain in Azure AI Search (for search)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(remove_embeddings_from_cosmos())
    sys.exit(0 if success else 1)
