"""Generate embeddings for all influencers and update Cosmos DB and Azure AI Search."""
import asyncio
import sys
import os
import json
from typing import List, Dict, Any, Set
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.cosmos_db import CosmosDBClient
from app.db.azure_search_store import AzureSearchStore
from app.services.embedding_service import EmbeddingService
from app.utils.batch_processor import process_batch_async
from app.core.config import settings
from tqdm import tqdm

# Progress tracking file
PROGRESS_FILE = Path("/tmp/embedding_generation_progress.json")


async def generate_embeddings_for_all():
    """Generate embeddings for all influencers."""
    print("=" * 60)
    print("Generating Embeddings for All Influencers")
    print("=" * 60)
    
    # Initialize services
    cosmos_client = CosmosDBClient()
    search_store = AzureSearchStore()
    embedding_service = EmbeddingService()
    
    if not embedding_service.is_available():
        print("ERROR: Embedding service not available. Check Azure OpenAI configuration.")
        return False
    
    try:
        # Connect to Cosmos DB (synchronous for querying)
        cosmos_client.connect()
        
        # Load progress if exists
        progress = {
            "last_processed_id": None,
            "total_processed": 0,
            "total_skipped": 0,
            "total_failed": 0
        }
        
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, 'r') as f:
                    saved_progress = json.load(f)
                    progress.update(saved_progress)
                print(f"📂 Resuming from previous run...")
                print(f"   Last processed: {progress['total_processed']:,} influencers")
            except Exception as e:
                print(f"⚠️  Could not load progress file: {e}")
        
        # Get total count first (for progress tracking)
        print("Counting total influencers in Cosmos DB...")
        count_query = "SELECT VALUE COUNT(1) FROM c"
        count_result = list(cosmos_client.container.query_items(
            query=count_query,
            enable_cross_partition_query=True
        ))
        total_count = count_result[0] if count_result else 0
        print(f"Found {total_count:,} total influencers in Cosmos DB")
        
        # Check which influencers already have embeddings in Azure AI Search (cached check)
        print("\nChecking existing embeddings in Azure AI Search...")
        existing_ids: Set[str] = set()
        
        try:
            if not search_store.client:
                raise RuntimeError("Azure AI Search not configured")
            
            # Query Azure AI Search to get all existing document IDs
            print("  Querying Azure AI Search for existing document IDs...")
            count = 0
            for result in search_store.client.search(
                search_text="*",
                select=["id"],
                top=1000  # Process in pages of 1000
            ):
                doc_id = result.get("id")
                if doc_id:
                    existing_ids.add(str(doc_id))
                count += 1
                if count % 5000 == 0:
                    print(f"    Loaded {count:,} existing IDs...")
            
            print(f"✅ Found {len(existing_ids):,} influencers with existing embeddings in Azure AI Search")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not check existing embeddings: {e}")
            print("   Will check per-batch instead...")
            existing_ids = set()  # Will check per batch
        
        # Now connect async for updates
        await cosmos_client.connect_async()
        
        # Process in batches from Cosmos DB (don't load all into memory)
        cosmos_batch_size = 1000  # Fetch 1000 influencers at a time from Cosmos DB
        embedding_batch_size = max(settings.EMBEDDING_BATCH_SIZE, 200)  # Process 200 embeddings at a time
        
        processed = progress["total_processed"]
        skipped = progress["total_skipped"]
        failed = progress["total_failed"]
        
        async def process_embedding_batch(batch: List[Dict[str, Any]]) -> tuple[int, int]:
            """Process a batch of influencers for embedding generation."""
            nonlocal processed, skipped, failed
            
            # Filter out influencers that already have embeddings
            to_process = []
            for inf in batch:
                inf_id = str(inf.get("id", inf.get("influencer_id", "")))
                if inf_id not in existing_ids:
                    to_process.append(inf)
                else:
                    skipped += 1
            
            if not to_process:
                return len(batch), 0  # All skipped
            
            # Prepare texts for embedding
            texts = []
            for inf in to_process:
                name = inf.get("name", "")
                username = inf.get("username", "")
                categories = inf.get("interest_categories", [])
                text = embedding_service.generate_embedding_text(name, username, categories)
                texts.append(text)
            
            # Generate embeddings
            try:
                embeddings = await embedding_service.generate_embeddings_batch(texts)
            except Exception as e:
                print(f"⚠️  Error generating embeddings for batch: {e}")
                # Return failed count for all items
                failed += len(to_process)
                return 0, len(to_process)
            
            # Prepare search documents (embeddings stored ONLY in Azure AI Search)
            search_docs = []
            batch_processed = 0
            batch_failed = 0
            
            for inf, embedding in zip(to_process, embeddings):
                if embedding and isinstance(embedding, list) and len(embedding) > 0:
                    # Verify embedding dimension (should be 3072 for text-embedding-3-large)
                    if len(embedding) != 3072:
                        print(f"⚠️  Warning: Embedding dimension mismatch for {inf.get('id')}: {len(embedding)} (expected 3072)")
                        batch_failed += 1
                        continue
                    
                    # Prepare search document (embedding stored ONLY in Azure AI Search)
                    try:
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
                            "embedding": embedding,  # Embedding stored ONLY in Azure AI Search
                        }
                        search_docs.append(search_doc)
                        batch_processed += 1
                    except Exception as e:
                        print(f"⚠️  Error preparing search doc for {inf.get('id')}: {e}")
                        batch_failed += 1
                else:
                    batch_failed += 1
            
            # Update Azure AI Search
            if search_docs:
                try:
                    search_store.upsert_documents(search_docs)
                    # Update existing_ids set to avoid re-checking
                    for doc in search_docs:
                        existing_ids.add(str(doc["id"]))
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error updating Azure AI Search: {error_msg}")
                    print(f"   Failed to upsert {len(search_docs)} documents")
                    
                    # Check if it's a storage quota error
                    if "quota" in error_msg.lower() or "storage" in error_msg.lower():
                        print("\n" + "=" * 60)
                        print("⚠️  AZURE AI SEARCH STORAGE QUOTA EXCEEDED")
                        print("=" * 60)
                        print("The Azure AI Search service has run out of storage space.")
                        print("\nSolutions:")
                        print("1. Upgrade Azure AI Search SKU in Azure Portal")
                        print("2. Delete old/unused documents from Azure AI Search")
                        print("3. Check storage usage in Azure Portal")
                        print("\nScript will continue but will fail until storage is increased.")
                        print("=" * 60 + "\n")
                    
                    # Don't count as processed if upsert failed
                    batch_failed += len(search_docs)
                    batch_processed -= len(search_docs)
            
            processed += batch_processed
            failed += batch_failed
            
            return batch_processed, batch_failed
        
        # Process Cosmos DB in batches (streaming approach)
        print(f"\n📦 Processing Cosmos DB in batches of {cosmos_batch_size}...")
        print(f"📊 Embedding batch size: {embedding_batch_size}")
        print(f"🔄 Concurrent batches: 3")
        print(f"📈 Total to process: {total_count:,} influencers")
        
        # Query Cosmos DB in batches using OFFSET
        offset = 0
        total_processed_in_session = 0
        
        with tqdm(total=total_count, desc="Generating embeddings", initial=processed) as pbar:
            while offset < total_count:
                # Fetch batch from Cosmos DB using OFFSET/LIMIT
                # Cosmos DB SQL API supports OFFSET and LIMIT
                batch_query = f"SELECT * FROM c OFFSET {offset} LIMIT {cosmos_batch_size}"
                try:
                    batch_influencers = list(cosmos_client.container.query_items(
                        query=batch_query,
                        enable_cross_partition_query=True
                    ))
                except Exception as e:
                    print(f"⚠️  Error fetching batch at offset {offset}: {e}")
                    print("   This might indicate OFFSET/LIMIT is not supported or a query error.")
                    print("   Continuing with next batch...")
                    offset += cosmos_batch_size
                    continue
                
                if not batch_influencers:
                    break
                
                # Process this batch in smaller embedding batches
                embedding_batches = [batch_influencers[i:i + embedding_batch_size] 
                                   for i in range(0, len(batch_influencers), embedding_batch_size)]
                
                # Process embedding batches concurrently (3 at a time)
                concurrent_embedding_batches = 3
                for i in range(0, len(embedding_batches), concurrent_embedding_batches):
                    batch_group = embedding_batches[i:i + concurrent_embedding_batches]
                    try:
                        results = await asyncio.gather(*[process_embedding_batch(batch) for batch in batch_group], return_exceptions=True)
                        
                        # Handle results (some might be exceptions)
                        for result in results:
                            if isinstance(result, Exception):
                                print(f"❌ Error in batch processing: {result}")
                                # Count as failed (approximate)
                                batch_size_approx = len(batch_group[0]) if batch_group else 0
                                failed += batch_size_approx
                            else:
                                proc, fail = result
                                pbar.update(proc)
                                total_processed_in_session += proc
                    except Exception as e:
                        print(f"❌ Error processing batch group: {e}")
                        # Count entire batch group as failed
                        failed += sum(len(batch) for batch in batch_group)
                    
                    # Save progress periodically (every 1000 processed or every batch)
                    if total_processed_in_session % 1000 == 0 or (i + concurrent_embedding_batches) >= len(embedding_batches):
                        progress["total_processed"] = processed
                        progress["total_skipped"] = skipped
                        progress["total_failed"] = failed
                        progress["last_processed_id"] = batch_influencers[-1].get("id") if batch_influencers else None
                        
                        try:
                            with open(PROGRESS_FILE, 'w') as f:
                                json.dump(progress, f, indent=2)
                        except Exception as e:
                            print(f"⚠️  Could not save progress: {e}")
                
                offset += len(batch_influencers)
                
                # Update progress file after each Cosmos DB batch
                progress["total_processed"] = processed
                progress["total_skipped"] = skipped
                progress["total_failed"] = failed
                progress["last_processed_id"] = batch_influencers[-1].get("id") if batch_influencers else None
                
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump(progress, f, indent=2)
        
        # Final summary
        print("\n" + "=" * 60)
        print("Embedding Generation Complete")
        print("=" * 60)
        print(f"Total influencers: {total_count:,}")
        print(f"Already had embeddings: {skipped:,}")
        print(f"Successfully generated: {processed:,}")
        print(f"Failed: {failed:,}")
        if (processed + skipped) > 0:
            success_rate = (processed / (processed + skipped + failed) * 100) if (processed + skipped + failed) > 0 else 0
            print(f"Success rate: {success_rate:.2f}%")
        print(f"\n✅ Total with embeddings in Azure AI Search: {skipped + processed:,} / {total_count:,}")
        
        # Clean up progress file on successful completion
        if PROGRESS_FILE.exists() and (processed + skipped) >= total_count * 0.99:  # 99% complete
            PROGRESS_FILE.unlink()
            print(f"\n🧹 Progress file cleaned up (completion > 99%)")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to generate embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up async client sessions to prevent "Unclosed client session" warnings
        try:
            if 'embedding_service' in locals():
                await embedding_service.close()
        except Exception as e:
            print(f"⚠️  Warning: Error closing embedding service: {e}")
        
        # Close Cosmos DB async client
        try:
            if 'cosmos_client' in locals() and cosmos_client.async_client:
                await cosmos_client.async_client.__aexit__(None, None, None)
        except Exception as e:
            # Try alternative close method
            try:
                if hasattr(cosmos_client.async_client, 'close'):
                    await cosmos_client.async_client.close()
            except:
                pass


if __name__ == "__main__":
    success = asyncio.run(generate_embeddings_for_all())
    sys.exit(0 if success else 1)
