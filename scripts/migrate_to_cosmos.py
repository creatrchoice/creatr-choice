"""Migration script from MongoDB to Cosmos DB."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_migration import DataMigrationService
from app.core.config import settings


async def main():
    """Main migration function - can be called from other scripts."""
    """Main migration function."""
    print("=" * 60)
    print("MongoDB to Azure Cosmos DB Migration")
    print("=" * 60)
    print()
    
    # Check configuration
    if not settings.LOCAL_MONGODB_URI:
        print("ERROR: LOCAL_MONGODB_URI not configured")
        return
    
    if not settings.AZURE_COSMOS_ENDPOINT or not settings.AZURE_COSMOS_KEY:
        print("ERROR: Azure Cosmos DB credentials not configured")
        return
    
    print(f"MongoDB URI: {settings.LOCAL_MONGODB_URI}")
    print(f"MongoDB Database: {settings.LOCAL_MONGODB_DATABASE}")
    print(f"MongoDB Collection: {settings.LOCAL_MONGODB_COLLECTION}")
    print()
    print(f"Cosmos DB Endpoint: {settings.AZURE_COSMOS_ENDPOINT}")
    print(f"Cosmos DB Database: {settings.AZURE_COSMOS_DATABASE}")
    print(f"Cosmos DB Container: {settings.AZURE_COSMOS_CONTAINER}")
    print()
    
    # Confirm
    response = input("Proceed with migration? (yes/no): ")
    if response.lower() != "yes":
        print("Migration cancelled.")
        return
    
    # Run migration
    migration_service = DataMigrationService()
    
    try:
        stats = await migration_service.migrate_all(
            batch_size=settings.MIGRATION_BATCH_SIZE,
            generate_embeddings=False  # Can be done separately
        )
        
        print()
        print("=" * 60)
        print("Migration Complete")
        print("=" * 60)
        print(f"Total Records: {stats['total_records']}")
        print(f"Migrated: {stats['migrated']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        
        if stats['failed_records']:
            print(f"\nFirst 10 Failed Records:")
            for record in stats['failed_records'][:10]:
                print(f"  ID: {record.get('id')}, Error: {record.get('error')}")
    
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()


async def run_migration():
    """Run migration - can be called from other scripts."""
    return await main()


if __name__ == "__main__":
    asyncio.run(main())
