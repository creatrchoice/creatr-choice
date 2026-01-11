"""Production-ready NLP agent for query understanding using LangChain."""
from typing import Optional
import logging
import json
import asyncio
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import LangChainException
from app.core.config import settings
from app.models.query_analysis import QueryAnalysisResult, ExtractedFilters
from app.models.categories import CategoryMetadata
from app.services.category_discovery import CategoryDiscoveryService
from app.prompts.query_analysis_prompt import get_query_analysis_prompt

logger = logging.getLogger(__name__)


class NLPAgent:
    """Production-ready NLP agent for understanding natural language queries using LangChain."""
    
    def __init__(self):
        """Initialize NLP agent with LangChain."""
        self.azure_llm: Optional[AzureChatOpenAI] = None
        self.openai_llm: Optional[ChatOpenAI] = None
        self.category_service = CategoryDiscoveryService()
        self.json_parser = JsonOutputParser(pydantic_object=QueryAnalysisResult)
        self._initialize_llms()
    
    def _initialize_llms(self) -> None:
        """Initialize LangChain LLM clients."""
        try:
            # Azure OpenAI (primary)
            if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
                self.azure_llm = AzureChatOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    temperature=settings.NLP_AGENT_TEMPERATURE,
                    max_tokens=settings.NLP_AGENT_MAX_TOKENS,
                    model_kwargs={"response_format": {"type": "json_object"}},
                    timeout=60,  # Production timeout
                    max_retries=3,  # Production retry logic
                )
                logger.info("Azure OpenAI LLM initialized successfully")
            
            # OpenAI (fallback)
            if settings.OPENAI_API_KEY and not self.azure_llm:
                self.openai_llm = ChatOpenAI(
                    model="gpt-4o",
                    temperature=settings.NLP_AGENT_TEMPERATURE,
                    max_tokens=settings.NLP_AGENT_MAX_TOKENS,
                    model_kwargs={"response_format": {"type": "json_object"}},
                )
                logger.info("OpenAI LLM initialized as fallback")
            
            if not self.azure_llm and not self.openai_llm:
                logger.warning("No LLM provider configured")
        
        except Exception as e:
            logger.error(f"Error initializing NLP agent: {e}", exc_info=True)
            raise
    
    def _create_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
        """
        Create LangChain prompt template.
        
        Args:
            system_prompt: System prompt content
        
        Returns:
            ChatPromptTemplate
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template("{query}"),
        ])
    
    async def analyze_query(self, query: str) -> QueryAnalysisResult:
        """
        Analyze natural language query and extract search parameters.
        
        Args:
            query: Natural language search query
        
        Returns:
            QueryAnalysisResult with extracted filters
        
        Raises:
            ValueError: If no LLM provider is configured
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for analysis")
            return self._create_default_result(query)
        
        try:
            # Get available categories (with timeout to prevent hanging)
            import asyncio
            try:
                categories = await asyncio.wait_for(
                    self.category_service.get_categories(),
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Category service timeout, using empty categories")
                # Use empty categories if timeout
                from app.models.categories import CategoryMetadata
                categories = CategoryMetadata(
                    interest_categories=[],
                    primary_categories=[],
                    cities=[],
                    creator_types=[],
                    platforms=[],
                    total_influencers=0
                )
            
            # Get system prompt
            system_prompt = get_query_analysis_prompt(categories)
            
            # Create prompt template
            prompt_template = self._create_prompt_template(system_prompt)
            
            # Select LLM
            llm = self.azure_llm or self.openai_llm
            if not llm:
                raise ValueError("No LLM provider configured")
            
            # Create chain
            chain = prompt_template | llm | self.json_parser
            
            # Invoke chain
            logger.info(f"Analyzing query: {query[:100]}...")
            result_dict = await chain.ainvoke({"query": query})
            
            # Validate and parse result
            result = QueryAnalysisResult(**result_dict)
            logger.info(
                f"Query analysis completed",
                extra={
                    "confidence": result.confidence,
                    "categories": result.extracted_filters.interest_categories,
                }
            )
            
            return result
        
        except LangChainException as e:
            logger.error(f"LangChain error analyzing query: {e}", exc_info=True)
            return self._create_default_result(query)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}", exc_info=True)
            return self._create_default_result(query)
        
        except Exception as e:
            logger.error(f"Unexpected error analyzing query: {e}", exc_info=True)
            return self._create_default_result(query)
    
    def _create_default_result(self, query: str) -> QueryAnalysisResult:
        """
        Create default result for error cases.
        
        Args:
            query: Original query
        
        Returns:
            QueryAnalysisResult with empty filters
        """
        return QueryAnalysisResult(
            search_intent="Unable to analyze query due to an error",
            extracted_filters=ExtractedFilters(),
            confidence=0.0,
            original_query=query,
        )
    
    def is_available(self) -> bool:
        """
        Check if NLP agent is available.
        
        Returns:
            True if at least one LLM provider is configured
        """
        return self.azure_llm is not None or self.openai_llm is not None
    
    async def close(self) -> None:
        """
        Close all async client sessions to prevent resource leaks.
        
        This should be called when done using the service to properly
        clean up aiohttp client sessions used by LangChain.
        """
        try:
            import asyncio
            # LangChain LLM clients use aiohttp internally
            if self.azure_llm:
                client = getattr(self.azure_llm, 'client', None)
                if client and hasattr(client, 'close'):
                    try:
                        close_method = client.close
                        if asyncio.iscoroutinefunction(close_method):
                            await close_method()
                        else:
                            close_method()
                    except Exception:
                        pass
            
            if self.openai_llm:
                client = getattr(self.openai_llm, 'client', None)
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
            logger.warning(f"Error closing NLP agent clients: {e}")