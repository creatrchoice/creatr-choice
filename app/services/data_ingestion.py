"""Data ingestion service for Cosmos DB."""
from typing import List, Dict, Any
from app.db.cosmos_db import CosmosDBClient
from app.utils.data_parser import normalize_influencer_data, validate_influencer_data
from app.models.influencer_data import InfluencerData
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.db.azure_search_store import AzureSearchStore


class DataIngestionService:
    """Service for ingesting influencer data into Cosmos DB and Azure AI Search."""
    
    def __init__(self):
        """Initialize ingestion service."""
        self.cosmos_client = CosmosDBClient()
        self.embedding_service = EmbeddingService()
        self.search_store = AzureSearchStore()
    
    async def ingest_influencer(
        self,
        data: Dict[str, Any],
        generate_embedding: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest a single influencer record.
        
        Args:
            data: Raw influencer data
            generate_embedding: Whether to generate and store embedding
        
        Returns:
            Created influencer document
        """
        # Normalize data
        normalized = normalize_influencer_data(data)
        
        # Validate
        is_valid, error = validate_influencer_data(normalized)
        if not is_valid:
            raise ValueError(f"Validation failed: {error}")
        
        # Convert to Pydantic model
        influencer_data = InfluencerData(**normalized)
        
        # Convert to dict for Cosmos DB
        doc = influencer_data.model_dump()
        doc["id"] = str(doc["id"])
        
        # Ensure platform is set for partition key
        if "platform" not in doc or not doc["platform"]:
            doc["platform"] = "instagram"
        
        # Generate embedding if requested (stored ONLY in Azure AI Search, not Cosmos DB)
        if generate_embedding:
            embedding_text = self.embedding_service.generate_embedding_text(
                name=doc.get("name", ""),
                username=doc.get("username", ""),
                categories=doc.get("interest_categories", [])
            )
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            
            if embedding:
                # NOTE: Embedding NOT stored in Cosmos DB - only metadata
                # Embeddings stored ONLY in Azure AI Search for fast vector search
                # This reduces storage costs and write operations
                
                # Store in Azure AI Search (with embedding)
                search_doc = {
                    "id": doc["id"],
                    "influencer_id": doc.get("influencer_id"),
                    "name": doc.get("name"),
                    "username": doc.get("username"),
                    "platform": doc.get("platform"),
                    "city": doc.get("city"),
                    "creator_type": doc.get("creator_type"),
                    "followers_count": doc.get("followers_count"),
                    "engagement_rate_value": doc.get("engagement_rate_value"),
                    "interest_categories": doc.get("interest_categories", []),
                    "primary_category": doc.get("primary_category", {}).get("name") if isinstance(doc.get("primary_category"), dict) else doc.get("primary_category"),
                    "embedding": embedding,  # Embedding stored ONLY in Azure AI Search
                }
                
                try:
                    self.search_store.upsert_documents([search_doc])
                except Exception as e:
                    print(f"Error upserting to Azure AI Search: {e}")
        
        # Store in Cosmos DB
        await self.cosmos_client.connect_async()
        created = await self.cosmos_client._create_item_async(doc)
        
        return created
    
    async def ingest_batch(
        self,
        records: List[Dict[str, Any]],
        generate_embeddings: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Ingest a batch of influencer records.
        
        Args:
            records: List of raw influencer data
            generate_embeddings: Whether to generate embeddings
        
        Returns:
            List of created documents
        """
        normalized_records = []
        search_docs = []
        
        for record in records:
            try:
                # Normalize and validate
                normalized = normalize_influencer_data(record)
                is_valid, error = validate_influencer_data(normalized)
                
                if not is_valid:
                    print(f"Skipping invalid record {normalized.get('id')}: {error}")
                    continue
                
                # Convert to Pydantic model
                influencer_data = InfluencerData(**normalized)
                doc = influencer_data.model_dump()
                doc["id"] = str(doc["id"])
                
                if "platform" not in doc or not doc["platform"]:
                    doc["platform"] = "instagram"
                
                # Generate embedding
                if generate_embeddings:
                    embedding_text = self.embedding_service.generate_embedding_text(
                        name=doc.get("name", ""),
                        username=doc.get("username", ""),
                        categories=doc.get("interest_categories", [])
                    )
                    embedding = await self.embedding_service.generate_embedding(embedding_text)
                    
                    if embedding:
                        doc["embedding"] = embedding
                        
                        search_doc = {
                            "id": doc["id"],
                            "influencer_id": doc.get("influencer_id"),
                            "name": doc.get("name"),
                            "username": doc.get("username"),
                            "platform": doc.get("platform"),
                            "city": doc.get("city"),
                            "creator_type": doc.get("creator_type"),
                            "followers_count": doc.get("followers_count"),
                            "engagement_rate_value": doc.get("engagement_rate_value"),
                            "interest_categories": doc.get("interest_categories", []),
                            "primary_category": doc.get("primary_category", {}).get("name") if isinstance(doc.get("primary_category"), dict) else doc.get("primary_category"),
                            "embedding": embedding,
                        }
                        search_docs.append(search_doc)
                
                normalized_records.append(doc)
            
            except Exception as e:
                print(f"Error processing record {record.get('id')}: {e}")
                continue
        
        # Bulk insert to Cosmos DB
        await self.cosmos_client.connect_async()
        created = await self.cosmos_client.bulk_create_items_async(normalized_records)
        
        # Bulk upsert to Azure AI Search
        if search_docs:
            try:
                self.search_store.upsert_documents(search_docs)
            except Exception as e:
                print(f"Error upserting to Azure AI Search: {e}")
        
        return created
