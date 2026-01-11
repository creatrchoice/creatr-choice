"""MongoDB reader for migration."""
from typing import Iterator, Dict, Any, Optional
import pymongo
from pymongo import MongoClient
from app.core.config import settings


class MongoDBReader:
    """Reader for local MongoDB during migration."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
    
    def connect(self) -> None:
        """Connect to MongoDB."""
        if not settings.LOCAL_MONGODB_URI:
            raise ValueError("LOCAL_MONGODB_URI not configured")
        
        self.client = MongoClient(settings.LOCAL_MONGODB_URI)
        self.db = self.client[settings.LOCAL_MONGODB_DATABASE]
        self.collection = self.db[settings.LOCAL_MONGODB_COLLECTION]
    
    def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
    
    def count_documents(self) -> int:
        """Count total documents in collection."""
        if self.collection is None:
            raise RuntimeError("Not connected to MongoDB")
        return self.collection.count_documents({})
    
    def read_batch(self, skip: int = 0, limit: int = 1000) -> list[Dict[str, Any]]:
        """
        Read a batch of documents.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
        
        Returns:
            List of documents
        """
        if self.collection is None:
            raise RuntimeError("Not connected to MongoDB")
        
        cursor = self.collection.find({}).skip(skip).limit(limit)
        return list(cursor)
    
    def read_all(self, batch_size: int = 1000) -> Iterator[list[Dict[str, Any]]]:
        """
        Read all documents in batches.
        
        Args:
            batch_size: Number of documents per batch
        
        Yields:
            Batches of documents
        """
        if self.collection is None:
            raise RuntimeError("Not connected to MongoDB")
        
        skip = 0
        while True:
            batch = self.read_batch(skip=skip, limit=batch_size)
            if not batch:
                break
            yield batch
            skip += len(batch)
            if len(batch) < batch_size:
                break
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
