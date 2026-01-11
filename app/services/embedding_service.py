"""Production-ready embedding generation service using LangChain."""
from typing import List, Optional
import logging
import asyncio
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from app.core.config import settings
from app.core.embeddings import embedding_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Production-ready service for generating embeddings using LangChain."""
    
    def __init__(self):
        """Initialize embedding service with LangChain."""
        self.azure_embeddings: Optional[AzureOpenAIEmbeddings] = None
        self.openai_embeddings: Optional[OpenAIEmbeddings] = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self) -> None:
        """Initialize LangChain embedding clients."""
        try:
            # Azure OpenAI (primary)
            if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
                self.azure_embeddings = AzureOpenAIEmbeddings(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    azure_deployment=embedding_config.model_name,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    chunk_size=16,  # Optimize for batch processing
                )
                logger.info("Azure OpenAI embeddings initialized successfully")
            
            # OpenAI (fallback)
            if settings.OPENAI_API_KEY and not self.azure_embeddings:
                self.openai_embeddings = OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=settings.OPENAI_API_KEY,
                    chunk_size=16,
                )
                logger.info("OpenAI embeddings initialized as fallback")
            
            if not self.azure_embeddings and not self.openai_embeddings:
                logger.warning("No embedding provider configured")
        
        except Exception as e:
            logger.error(f"Error initializing embedding service: {e}", exc_info=True)
            raise
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector or None if error
        
        Raises:
            ValueError: If no embedding provider is configured
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
        
        try:
            # Use Azure OpenAI (primary)
            if self.azure_embeddings:
                embedding = await self.azure_embeddings.aembed_query(text)
                logger.debug(f"Generated embedding for text (length: {len(text)})")
                return embedding
            
            # Fallback to OpenAI
            if self.openai_embeddings:
                embedding = await self.openai_embeddings.aembed_query(text)
                logger.debug(f"Generated embedding using OpenAI fallback")
                return embedding
            
            raise ValueError("No embedding provider configured")
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None
    
    async def generate_embeddings_batch(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts with batch processing.
        
        Args:
            texts: List of texts to embed
            batch_size: Optional batch size (uses config default if not provided)
        
        Returns:
            List of embedding vectors (None for failed embeddings)
        """
        if not texts:
            return []
        
        # Filter out empty texts and track indices
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
        
        if not valid_texts:
            logger.warning("No valid texts provided for batch embedding")
            return [None] * len(texts)
        
        batch_size = batch_size or embedding_config.batch_size
        
        try:
            # Extract valid texts for processing
            texts_to_embed = [text for _, text in valid_texts]
            
            # Use Azure OpenAI (primary)
            if self.azure_embeddings:
                embeddings = await self.azure_embeddings.aembed_documents(
                    texts_to_embed
                )
                logger.info(f"Generated {len(embeddings)} embeddings using Azure OpenAI")
            
            # Fallback to OpenAI
            elif self.openai_embeddings:
                embeddings = await self.openai_embeddings.aembed_documents(
                    texts_to_embed
                )
                logger.info(f"Generated {len(embeddings)} embeddings using OpenAI fallback")
            
            else:
                raise ValueError("No embedding provider configured")
            
            # Map embeddings back to original positions
            result = [None] * len(texts)
            for (idx, _), embedding in zip(valid_texts, embeddings):
                result[idx] = embedding
            
            return result
        
        except Exception as e:
            logger.error(
                f"Error generating batch embeddings: {e}",
                exc_info=True,
                extra={"text_count": len(texts), "valid_count": len(valid_texts)}
            )
            return [None] * len(texts)
    
    def generate_embedding_text(
        self, name: str, username: str, categories: List[str]
    ) -> str:
        """
        Generate text for embedding from influencer data.
        
        Args:
            name: Influencer name
            username: Username
            categories: List of interest categories
        
        Returns:
            Combined text for embedding
        """
        return embedding_config.get_embedding_text(name, username, categories)
    
    def is_available(self) -> bool:
        """
        Check if embedding service is available.
        
        Returns:
            True if at least one provider is configured
        """
        return self.azure_embeddings is not None or self.openai_embeddings is not None
    
    async def close(self) -> None:
        """
        Close all async client sessions to prevent resource leaks.
        
        This should be called when done using the service to properly
        clean up aiohttp client sessions used by LangChain.
        """
        try:
            # LangChain clients use aiohttp internally via httpx or openai clients
            # The underlying clients are typically accessed through the client attribute
            if self.azure_embeddings:
                # Try to access and close the underlying HTTP client
                client = getattr(self.azure_embeddings, 'client', None)
                if client:
                    # Check if it's an async client with a close method
                    if hasattr(client, 'close'):
                        if callable(getattr(client, 'close', None)):
                            close_method = client.close
                            # Check if it's async
                            if hasattr(close_method, '__call__'):
                                try:
                                    if asyncio.iscoroutinefunction(close_method):
                                        await close_method()
                                    else:
                                        close_method()
                                except Exception:
                                    pass
            
            if self.openai_embeddings:
                client = getattr(self.openai_embeddings, 'client', None)
                if client and hasattr(client, 'close'):
                    try:
                        close_method = client.close
                        if asyncio.iscoroutinefunction(close_method):
                            await close_method()
                        else:
                            close_method()
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Error closing embedding service clients: {e}")
