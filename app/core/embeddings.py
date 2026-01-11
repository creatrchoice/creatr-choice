"""Embedding model configuration."""
from enum import Enum
from typing import Optional
from app.core.config import settings


class EmbeddingProvider(str, Enum):
    """Embedding provider options."""
    AZURE_OPENAI = "azure_openai"
    OPENAI = "openai"


class EmbeddingConfig:
    """Configuration for embedding generation."""
    
    def __init__(self):
        self.provider = EmbeddingProvider.AZURE_OPENAI
        self.dimensions = 768
        self.model_name = "text-embedding-3-large"
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
    
    @property
    def azure_endpoint(self) -> Optional[str]:
        """Azure OpenAI endpoint."""
        return settings.AZURE_OPENAI_ENDPOINT if settings.AZURE_OPENAI_ENDPOINT else None
    
    @property
    def azure_api_key(self) -> Optional[str]:
        """Azure OpenAI API key."""
        return settings.AZURE_OPENAI_API_KEY if settings.AZURE_OPENAI_API_KEY else None
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API key (fallback)."""
        return settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else None
    
    def get_embedding_text(self, name: str, username: str, categories: list) -> str:
        """
        Generate text for embedding from influencer data.
        
        Args:
            name: Influencer name
            username: Username
            categories: List of interest categories
        
        Returns:
            Combined text for embedding
        """
        category_text = " ".join(categories) if categories else ""
        return f"{name} {username} {category_text}".strip()


embedding_config = EmbeddingConfig()
