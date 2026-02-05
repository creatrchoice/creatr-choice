"""Application configuration."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Influencer Discovery API"
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string or single value
            if v.strip() == "*":
                return ["*"]
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else ["*"]
    
    # Azure Cosmos DB
    AZURE_COSMOS_ENDPOINT: str = ""
    AZURE_COSMOS_KEY: str = ""
    AZURE_COSMOS_DATABASE: str = "influencer_db"
    
    # Cosmos DB Containers (4-collection architecture)
    AZURE_COSMOS_CONTAINER: str = "influencers"  # Legacy, kept for backward compatibility
    AZURE_COSMOS_INFLUENCERS_CONTAINER: str = "influencers"
    AZURE_COSMOS_FREE_INFLUENCERS_CONTAINER: str = "free_influencers"
    AZURE_COSMOS_BRANDS_CONTAINER: str = "brands"
    AZURE_COSMOS_BRAND_COLLABORATIONS_CONTAINER: str = "brand_collaborations"
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "influencers-index"
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "text-embedding-3-large"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-4o"  # For NLP agent
    
    # Azure Storage
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "uploads"
    
    # OpenAI (fallback)
    OPENAI_API_KEY: str = ""
    
    # Local MongoDB (for migration)
    LOCAL_MONGODB_URI: str = "mongodb://localhost:27017"
    LOCAL_MONGODB_DATABASE: str = ""
    LOCAL_MONGODB_COLLECTION: str = ""
    
    # External APIs (for future integrations)
    TWITTER_API_KEY: str = ""
    INSTAGRAM_API_KEY: str = ""
    RAPIDAPI_KEY: str = ""
    
    # Search Configuration
    SEARCH_BATCH_SIZE: int = 100
    EMBEDDING_BATCH_SIZE: int = 100
    MIGRATION_BATCH_SIZE: int = 1000
    RRF_WEIGHT_KEYWORD: float = 0.4
    RRF_WEIGHT_VECTOR: float = 0.6
    
    # AI Agent Configuration
    NLP_AGENT_TEMPERATURE: float = 0.3
    NLP_AGENT_MAX_TOKENS: int = 1000
    
    # Application Settings
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()
