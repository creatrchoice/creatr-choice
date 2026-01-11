"""Setup validation script to check all Azure and local services."""
import asyncio
import sys
import os
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.cosmos_db import CosmosDBClient
from app.db.mongodb_reader import MongoDBReader
from app.services.embedding_service import EmbeddingService
from app.services.nlp_agent import NLPAgent
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from azure.cosmos import exceptions as cosmos_exceptions
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
import pymongo


class SetupChecker:
    """Check setup for all services."""
    
    def __init__(self):
        """Initialize checker."""
        self.results: List[Tuple[str, bool, str]] = []
    
    def log_result(self, service: str, success: bool, message: str = ""):
        """Log check result."""
        self.results.append((service, success, message))
        status = "✓" if success else "✗"
        print(f"{status} {service}: {message if message else ('OK' if success else 'FAILED')}")
    
    def check_cosmos_db(self) -> bool:
        """Check Azure Cosmos DB connection."""
        print("\n" + "="*60)
        print("Checking Azure Cosmos DB...")
        print("="*60)
        
        # Check configuration
        if not settings.AZURE_COSMOS_ENDPOINT:
            self.log_result("Cosmos DB Endpoint", False, "Not configured in .env")
            return False
        
        if not settings.AZURE_COSMOS_KEY:
            self.log_result("Cosmos DB Key", False, "Not configured in .env")
            return False
        
        self.log_result("Cosmos DB Config", True, "Configuration found")
        
        # Test connection
        try:
            client = CosmosDBClient()
            client.connect()
            self.log_result("Cosmos DB Connection", True, "Connected successfully")
            
            # Check database exists
            try:
                db = client.client.get_database_client(settings.AZURE_COSMOS_DATABASE)
                db.read()
                self.log_result("Cosmos DB Database", True, f"Database '{settings.AZURE_COSMOS_DATABASE}' exists")
            except cosmos_exceptions.CosmosHttpResponseError as e:
                if e.status_code == 404:
                    self.log_result("Cosmos DB Database", False, f"Database '{settings.AZURE_COSMOS_DATABASE}' not found")
                else:
                    self.log_result("Cosmos DB Database", False, f"Error: {e}")
            
            # Check container exists
            try:
                container = db.get_container_client(settings.AZURE_COSMOS_CONTAINER)
                container.read()
                self.log_result("Cosmos DB Container", True, f"Container '{settings.AZURE_COSMOS_CONTAINER}' exists")
                
                # Get item count
                query = "SELECT VALUE COUNT(1) FROM c"
                items = list(container.query_items(query=query, enable_cross_partition_query=True))
                count = items[0] if items else 0
                self.log_result("Cosmos DB Data", True, f"Found {count} items in container")
                
            except cosmos_exceptions.CosmosHttpResponseError as e:
                if e.status_code == 404:
                    self.log_result("Cosmos DB Container", False, f"Container '{settings.AZURE_COSMOS_CONTAINER}' not found")
                else:
                    self.log_result("Cosmos DB Container", False, f"Error: {e}")
            
            # CosmosClient doesn't have close() method - connection is managed automatically
            return True
            
        except Exception as e:
            self.log_result("Cosmos DB Connection", False, f"Connection failed: {str(e)}")
            return False
    
    def check_azure_search(self) -> bool:
        """Check Azure AI Search connection."""
        print("\n" + "="*60)
        print("Checking Azure AI Search...")
        print("="*60)
        
        # Check configuration
        if not settings.AZURE_SEARCH_ENDPOINT:
            self.log_result("Search Endpoint", False, "Not configured in .env")
            return False
        
        if not settings.AZURE_SEARCH_KEY:
            self.log_result("Search Key", False, "Not configured in .env")
            return False
        
        self.log_result("Search Config", True, "Configuration found")
        
        # Test connection
        try:
            credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
            client = SearchClient(
                endpoint=settings.AZURE_SEARCH_ENDPOINT,
                index_name=settings.AZURE_SEARCH_INDEX_NAME,
                credential=credential
            )
            
            # Test connection by trying to search
            self.log_result("Search Connection", True, "Connected successfully")
            
            # Check if index exists
            try:
                # Try a simple query to check index
                results = client.search(search_text="*", top=1)
                list(results)  # Consume iterator
                self.log_result("Search Index", True, f"Index '{settings.AZURE_SEARCH_INDEX_NAME}' exists and is accessible")
            except Exception as e:
                error_msg = str(e)
                if "index" in error_msg.lower() or "404" in error_msg:
                    self.log_result("Search Index", False, f"Index '{settings.AZURE_SEARCH_INDEX_NAME}' not found - run create_search_index.py")
                else:
                    self.log_result("Search Index", False, f"Index error: {error_msg}")
            
            return True
            
        except Exception as e:
            self.log_result("Search Connection", False, f"Connection failed: {str(e)}")
            return False
    
    async def check_azure_openai(self) -> bool:
        """Check Azure OpenAI connection and models."""
        print("\n" + "="*60)
        print("Checking Azure OpenAI...")
        print("="*60)
        
        # Check configuration
        if not settings.AZURE_OPENAI_ENDPOINT:
            self.log_result("OpenAI Endpoint", False, "Not configured in .env")
            return False
        
        if not settings.AZURE_OPENAI_API_KEY:
            self.log_result("OpenAI API Key", False, "Not configured in .env")
            return False
        
        self.log_result("OpenAI Config", True, "Configuration found")
        
        # Test embedding model
        try:
            embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )
            
            # Test embedding generation
            test_embedding = await embeddings.aembed_query("test")
            if test_embedding and len(test_embedding) > 0:
                self.log_result(
                    "Embedding Model",
                    True,
                    f"Model '{settings.AZURE_OPENAI_DEPLOYMENT_NAME}' working (dimension: {len(test_embedding)})"
                )
            else:
                self.log_result("Embedding Model", False, "Model returned empty embedding")
                return False
                
        except Exception as e:
            self.log_result("Embedding Model", False, f"Error: {str(e)}")
            return False
        
        # Test chat model
        try:
            chat = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                temperature=0.3,
                max_tokens=10,
            )
            
            # Test chat completion
            response = await chat.ainvoke("Say 'test'")
            if response and response.content:
                self.log_result(
                    "Chat Model",
                    True,
                    f"Model '{settings.AZURE_OPENAI_CHAT_DEPLOYMENT}' working"
                )
            else:
                self.log_result("Chat Model", False, "Model returned empty response")
                return False
                
        except Exception as e:
            self.log_result("Chat Model", False, f"Error: {str(e)}")
            return False
        
        return True
    
    def check_mongodb(self) -> bool:
        """Check local MongoDB connection."""
        print("\n" + "="*60)
        print("Checking Local MongoDB...")
        print("="*60)
        
        # Check configuration
        if not settings.LOCAL_MONGODB_URI:
            self.log_result("MongoDB URI", False, "Not configured in .env")
            return False
        
        self.log_result("MongoDB Config", True, "Configuration found")
        
        # Test connection
        try:
            client = pymongo.MongoClient(settings.LOCAL_MONGODB_URI, serverSelectionTimeoutMS=5000)
            client.server_info()  # Force connection
            self.log_result("MongoDB Connection", True, "Connected successfully")
            
            # Check database
            if settings.LOCAL_MONGODB_DATABASE:
                db = client[settings.LOCAL_MONGODB_DATABASE]
                collections = db.list_collection_names()
                self.log_result("MongoDB Database", True, f"Database '{settings.LOCAL_MONGODB_DATABASE}' exists")
                self.log_result("MongoDB Collections", True, f"Found {len(collections)} collections")
                
                # Check collection
                if settings.LOCAL_MONGODB_COLLECTION:
                    collection = db[settings.LOCAL_MONGODB_COLLECTION]
                    count = collection.count_documents({})
                    self.log_result("MongoDB Collection", True, f"Collection '{settings.LOCAL_MONGODB_COLLECTION}' exists with {count} documents")
                else:
                    self.log_result("MongoDB Collection", False, "Collection name not configured")
            else:
                self.log_result("MongoDB Database", False, "Database name not configured")
            
            client.close()
            return True
            
        except pymongo.errors.ServerSelectionTimeoutError:
            self.log_result("MongoDB Connection", False, "Connection timeout - MongoDB may not be running")
            return False
        except Exception as e:
            self.log_result("MongoDB Connection", False, f"Connection failed: {str(e)}")
            return False
    
    async def check_services(self) -> bool:
        """Check all services using service classes."""
        print("\n" + "="*60)
        print("Checking Service Classes...")
        print("="*60)
        
        # Check embedding service
        try:
            embedding_service = EmbeddingService()
            if embedding_service.is_available():
                test_embedding = await embedding_service.generate_embedding("test")
                if test_embedding:
                    self.log_result("Embedding Service", True, "Service working correctly")
                else:
                    self.log_result("Embedding Service", False, "Service available but returned None")
            else:
                self.log_result("Embedding Service", False, "Service not available")
        except Exception as e:
            self.log_result("Embedding Service", False, f"Error: {str(e)}")
        
        # Check NLP agent
        try:
            nlp_agent = NLPAgent()
            if nlp_agent.is_available():
                self.log_result("NLP Agent", True, "Service initialized correctly")
            else:
                self.log_result("NLP Agent", False, "Service not available")
        except Exception as e:
            self.log_result("NLP Agent", False, f"Error: {str(e)}")
        
        return True
    
    def print_summary(self):
        """Print summary of all checks."""
        print("\n" + "="*60)
        print("SETUP CHECK SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for _, success, _ in self.results if success)
        failed = total - passed
        
        print(f"\nTotal Checks: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        
        if failed > 0:
            print("\nFailed Checks:")
            for service, success, message in self.results:
                if not success:
                    print(f"  ✗ {service}: {message}")
        
        print("\n" + "="*60)
        
        if failed == 0:
            print("✓ All checks passed! Your setup is ready.")
            return True
        else:
            print("✗ Some checks failed. Please review the errors above.")
            return False


async def main():
    """Main function."""
    print("="*60)
    print("AI Influencer Discovery - Setup Validation")
    print("="*60)
    
    checker = SetupChecker()
    
    # Run all checks
    cosmos_ok = checker.check_cosmos_db()
    search_ok = checker.check_azure_search()
    openai_ok = await checker.check_azure_openai()
    mongodb_ok = checker.check_mongodb()
    await checker.check_services()
    
    # Print summary
    all_ok = checker.print_summary()
    
    # Exit code
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
