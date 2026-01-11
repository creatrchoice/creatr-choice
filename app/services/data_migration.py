"""Data migration service from MongoDB to Cosmos DB."""
from typing import List, Dict, Any
from datetime import datetime
from app.db.mongodb_reader import MongoDBReader
from app.db.cosmos_db import CosmosDBClient
from app.utils.data_parser import normalize_influencer_data, validate_influencer_data
from app.models.influencer_data import InfluencerData
from app.core.config import settings
import json


class DataMigrationService:
    """Service for migrating data from MongoDB to Cosmos DB."""
    
    def __init__(self):
        """Initialize migration service."""
        self.mongo_reader = MongoDBReader()
        self.cosmos_client = CosmosDBClient()
        self.migrated_count = 0
        self.failed_count = 0
        self.failed_records = []
    
    async def migrate_all(
        self,
        batch_size: int = None,
        generate_embeddings: bool = False,
    ) -> Dict[str, Any]:
        """
        Migrate all data from MongoDB to Cosmos DB.
        
        Args:
            batch_size: Batch size for processing
            generate_embeddings: Whether to generate embeddings during migration
        
        Returns:
            Migration statistics
        """
        batch_size = batch_size or settings.MIGRATION_BATCH_SIZE
        
        # Connect to MongoDB
        self.mongo_reader.connect()
        
        # Create Cosmos DB database and container
        self.cosmos_client.connect()
        self.cosmos_client.create_database_and_container_if_not_exists()
        
        # Get total count
        total_count = self.mongo_reader.count_documents()
        
        print(f"Starting migration of {total_count} records...")
        
        # Process in batches
        async def process_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Process a batch of records."""
            normalized_batch = []
            
            for record in batch:
                try:
                    # Normalize data
                    normalized = normalize_influencer_data(record)
                    
                    # Validate
                    is_valid, error = validate_influencer_data(normalized)
                    if not is_valid:
                        print(f"Validation failed for record {normalized.get('id')}: {error}")
                        self.failed_count += 1
                        self.failed_records.append({"id": normalized.get("id"), "error": error})
                        continue
                    
                    # Convert to Pydantic model for validation
                    influencer_data = InfluencerData(**normalized)
                    
                    # Convert back to dict for Cosmos DB with JSON serialization
                    # Use model_dump with mode='json' to handle datetime serialization
                    doc = influencer_data.model_dump(mode='json')
                    doc["id"] = str(doc["id"])
                    
                    # Ensure username is set (should be set by validator, but double-check)
                    if not doc.get("username"):
                        doc["username"] = f"user_{doc['id']}"
                    
                    # Ensure platform is set for partition key
                    if "platform" not in doc or not doc["platform"]:
                        doc["platform"] = "instagram"  # Default
                    
                    normalized_batch.append(doc)
                
                except Exception as e:
                    record_id = record.get("id") if isinstance(record, dict) else "unknown"
                    print(f"Error processing record {record_id}: {e}")
                    self.failed_count += 1
                    self.failed_records.append({"id": record_id, "error": str(e)})
            
            # Bulk insert to Cosmos DB
            if normalized_batch:
                try:
                    created = await self.cosmos_client.bulk_create_items_async(normalized_batch)
                    self.migrated_count += len(created)
                    print(f"Migrated batch: {len(created)} records (Total: {self.migrated_count})")
                except Exception as e:
                    print(f"Error inserting batch: {e}")
                    self.failed_count += len(normalized_batch)
            
            return normalized_batch
        
        # Read and process all batches directly
        total_batches = (total_count + batch_size - 1) // batch_size
        
        from tqdm import tqdm
        with tqdm(total=total_count, desc="Migrating to Cosmos DB") as pbar:
            for batch in self.mongo_reader.read_all(batch_size=batch_size):
                await process_batch(batch)
                pbar.update(len(batch))
        
        # Close connections
        self.mongo_reader.disconnect()
        self.cosmos_client.close()
        
        return {
            "total_records": total_count,
            "migrated": self.migrated_count,
            "failed": self.failed_count,
            "success_rate": (self.migrated_count / total_count * 100) if total_count > 0 else 0,
            "failed_records": self.failed_records[:100]  # Limit to first 100
        }
