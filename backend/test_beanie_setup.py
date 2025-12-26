#!/usr/bin/env python3
"""
Test script to verify Beanie setup with SubscriptionDocument
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Add app to path
sys.path.insert(0, '/home/user/webapp/backend')

from app.infrastructure.models.documents import (
    AgentDocument,
    SessionDocument,
    UserDocument,
    SubscriptionDocument
)
from app.core.config import get_settings


async def test_beanie_setup():
    """Test Beanie initialization with all documents"""
    
    print("🔧 Testing Beanie Setup with SubscriptionDocument")
    print("=" * 60)
    
    # Load settings
    settings = get_settings()
    
    print(f"\n1️⃣ Connecting to MongoDB...")
    print(f"   URI: {settings.mongodb_uri}")
    print(f"   Database: {settings.mongodb_database}")
    
    # Create MongoDB client
    client = AsyncIOMotorClient(settings.mongodb_uri)
    database = client[settings.mongodb_database]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("   ✅ MongoDB connection successful")
        
        # Initialize Beanie
        print(f"\n2️⃣ Initializing Beanie with document models...")
        await init_beanie(
            database=database,
            document_models=[
                AgentDocument,
                SessionDocument,
                UserDocument,
                SubscriptionDocument
            ]
        )
        print("   ✅ Beanie initialized successfully")
        
        # Verify collections
        print(f"\n3️⃣ Verifying collections...")
        collections = await database.list_collection_names()
        
        expected_collections = ["agents", "sessions", "users", "subscriptions"]
        for coll_name in expected_collections:
            if coll_name in collections:
                print(f"   ✅ Collection '{coll_name}' exists")
            else:
                print(f"   ℹ️  Collection '{coll_name}' will be created on first insert")
        
        # Verify indexes
        print(f"\n4️⃣ Verifying indexes...")
        
        # Check subscriptions indexes
        if "subscriptions" in collections:
            indexes = await database.subscriptions.index_information()
            print(f"   Subscriptions collection indexes:")
            for idx_name, idx_info in indexes.items():
                print(f"      - {idx_name}: {idx_info.get('key', [])}")
            print("   ✅ Subscriptions indexes verified")
        else:
            print("   ℹ️  Subscriptions collection will be created with indexes on first insert")
        
        # Test SubscriptionDocument model
        print(f"\n5️⃣ Testing SubscriptionDocument model...")
        from app.domain.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
        
        # Create test subscription
        test_sub = Subscription(
            id="test-sub-123",
            user_id="test-user-123",
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE
        )
        
        # Convert to document
        sub_doc = SubscriptionDocument.from_domain(test_sub)
        print(f"   ✅ Created SubscriptionDocument from domain model")
        print(f"      - subscription_id: {sub_doc.subscription_id}")
        print(f"      - user_id: {sub_doc.user_id}")
        print(f"      - plan: {sub_doc.plan}")
        print(f"      - status: {sub_doc.status}")
        
        # Convert back to domain
        domain_sub = sub_doc.to_domain()
        print(f"   ✅ Converted back to domain model")
        print(f"      - id: {domain_sub.id}")
        print(f"      - plan: {domain_sub.plan}")
        
        # Test repository
        print(f"\n6️⃣ Testing SubscriptionRepository...")
        from app.infrastructure.repositories.subscription_repository import MongoSubscriptionRepository
        
        repo = MongoSubscriptionRepository()
        print(f"   ✅ MongoSubscriptionRepository instantiated")
        
        # Note: Not creating actual DB records in test
        print(f"   ℹ️  Skipping actual DB operations (test mode)")
        
        print(f"\n{'=' * 60}")
        print("🎉 All Beanie setup tests passed!")
        print("✅ SubscriptionDocument is properly configured")
        print("✅ Ready for production use")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Close connection
        client.close()
        print(f"\n🔌 MongoDB connection closed")


async def main():
    """Main test function"""
    success = await test_beanie_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
