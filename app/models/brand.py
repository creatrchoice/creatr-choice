"""Brand data models."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Brand(BaseModel):
    """Brand model for Cosmos DB storage.

    Partition key: /id
    """
    id: str
    name: str
    logo: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    instaHandle: Optional[str] = None
    created_at: Optional[datetime] = None
