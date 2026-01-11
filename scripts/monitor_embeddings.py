"""Monitor embedding generation progress."""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.cosmos_db import CosmosDBClient
from app.db.azure_search_store import AzureSearchStore

PROGRESS_FILE = Path("/tmp/embedding_generation_progress.json")


def monitor_progress():
    """Monitor embedding generation progress."""
    print("=" * 60)
    print("Embedding Generation Progress Monitor")
    print("=" * 60)
    
    # Check if script is running
    import subprocess
    result = subprocess.run(
        ["ps", "aux"], 
        capture_output=True, 
        text=True
    )
    is_running = "generate_embeddings.py" in result.stdout
    
    if is_running:
        print("✅ Script is RUNNING")
    else:
        print("⚠️  Script is NOT running")
    
    # Check progress file
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            
            print(f"\n📊 Progress from file:")
            print(f"   Processed: {progress.get('total_processed', 0):,}")
            print(f"   Skipped: {progress.get('total_skipped', 0):,}")
            print(f"   Failed: {progress.get('total_failed', 0):,}")
            print(f"   Last ID: {progress.get('last_processed_id', 'N/A')}")
            
            total = progress.get('total_processed', 0) + progress.get('total_skipped', 0) + progress.get('total_failed', 0)
            if total > 0:
                success_rate = (progress.get('total_processed', 0) / total) * 100
                print(f"   Success rate: {success_rate:.2f}%")
        except Exception as e:
            print(f"⚠️  Could not read progress file: {e}")
    else:
        print("\n⚠️  No progress file found")
    
    # Check Cosmos DB count
    try:
        cosmos_client = CosmosDBClient()
        cosmos_client.connect()
        count_query = "SELECT VALUE COUNT(1) FROM c"
        count_result = list(cosmos_client.container.query_items(
            query=count_query,
            enable_cross_partition_query=True
        ))
        total_cosmos = count_result[0] if count_result else 0
        print(f"\n📦 Cosmos DB: {total_cosmos:,} influencers")
    except Exception as e:
        print(f"\n⚠️  Could not check Cosmos DB: {e}")
        total_cosmos = 0
    
    # Check Azure AI Search count
    try:
        search_store = AzureSearchStore()
        if search_store.client:
            search_count = 0
            for _ in search_store.client.search(search_text="*", select=["id"], top=1000):
                search_count += 1
                if search_count >= 1000:  # Limit check to first 1000
                    break
            
            print(f"🔍 Azure AI Search: {search_count:,}+ documents (checked first 1000)")
            
            if total_cosmos > 0:
                coverage = (search_count / total_cosmos) * 100 if search_count < 1000 else ">0.5"
                print(f"   Coverage: {coverage}%")
        else:
            print("⚠️  Azure AI Search not configured")
    except Exception as e:
        print(f"⚠️  Could not check Azure AI Search: {e}")
    
    # Estimate time remaining
    if PROGRESS_FILE.exists() and is_running:
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            
            processed = progress.get('total_processed', 0)
            if processed > 0 and total_cosmos > 0:
                remaining = total_cosmos - processed
                # Estimate ~10 items/second
                rate = 10
                seconds_remaining = remaining / rate
                hours = seconds_remaining / 3600
                minutes = (seconds_remaining % 3600) / 60
                
                print(f"\n⏱️  Estimated time remaining:")
                print(f"   Remaining: {remaining:,} influencers")
                print(f"   At {rate} items/sec: ~{int(hours)}h {int(minutes)}m")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("Monitor again with: python scripts/monitor_embeddings.py")
    print("=" * 60)


if __name__ == "__main__":
    monitor_progress()
