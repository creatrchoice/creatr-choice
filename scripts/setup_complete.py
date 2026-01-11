"""Complete setup script - orchestrates all setup tasks."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.check_setup import SetupChecker
from scripts.create_search_index import create_index
from scripts.migrate_to_cosmos import run_migration
from scripts.generate_embeddings import generate_embeddings_for_all


async def run_setup():
    """Run complete setup process."""
    print("=" * 60)
    print("AI Influencer Discovery - Complete Setup")
    print("=" * 60)
    print()
    
    # Step 1: Validate configuration
    print("Step 1: Validating Configuration...")
    print("-" * 60)
    checker = SetupChecker()
    
    # Check basic configs (skip actual connections for now)
    from app.core.config import settings
    
    config_ok = True
    if not settings.AZURE_COSMOS_ENDPOINT:
        print("✗ AZURE_COSMOS_ENDPOINT not configured")
        config_ok = False
    if not settings.AZURE_OPENAI_ENDPOINT:
        print("✗ AZURE_OPENAI_ENDPOINT not configured")
        config_ok = False
    if not settings.AZURE_SEARCH_ENDPOINT:
        print("✗ AZURE_SEARCH_ENDPOINT not configured")
        config_ok = False
    
    if not config_ok:
        print("\nERROR: Please configure all required settings in .env file")
        return False
    
    print("✓ Basic configuration validated")
    print()
    
    # Step 2: Create Azure AI Search Index
    print("Step 2: Creating Azure AI Search Index...")
    print("-" * 60)
    index_created = create_index()
    if not index_created:
        print("ERROR: Failed to create search index")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            return False
    print()
    
    # Step 3: Migrate data (optional)
    print("Step 3: Data Migration...")
    print("-" * 60)
    if settings.LOCAL_MONGODB_URI and settings.LOCAL_MONGODB_DATABASE:
        response = input("Do you want to migrate data from MongoDB? (yes/no): ")
        if response.lower() == "yes":
            print("Running migration...")
            try:
                await run_migration()
            except Exception as e:
                print(f"Migration error: {e}")
                response = input("Continue anyway? (yes/no): ")
                if response.lower() != "yes":
                    return False
        else:
            print("Skipping data migration")
    else:
        print("MongoDB not configured, skipping migration")
    print()
    
    # Step 4: Generate embeddings
    print("Step 4: Generating Embeddings...")
    print("-" * 60)
    response = input("Do you want to generate embeddings for all influencers? (yes/no): ")
    if response.lower() == "yes":
        embeddings_ok = await generate_embeddings_for_all()
        if not embeddings_ok:
            print("WARNING: Embedding generation had errors")
    else:
        print("Skipping embedding generation")
    print()
    
    # Step 5: Final validation
    print("Step 5: Final Validation...")
    print("-" * 60)
    all_ok = checker.print_summary()
    print()
    
    if all_ok:
        print("=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print("\nYou can now start the API with:")
        print("  uvicorn main:app --reload")
        print()
    else:
        print("=" * 60)
        print("⚠ Setup completed with warnings")
        print("=" * 60)
        print("\nPlease review the errors above and fix them before starting the API.")
        print()
    
    return all_ok


if __name__ == "__main__":
    success = asyncio.run(run_setup())
    sys.exit(0 if success else 1)
