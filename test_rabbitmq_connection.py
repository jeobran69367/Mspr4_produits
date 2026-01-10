#!/usr/bin/env python3
"""
RabbitMQ Connection Test Script for Railway
Usage: python test_rabbitmq_connection.py
"""
import asyncio
import os
import sys

# Add app to path dynamically
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.events.producer import event_producer
from app.events.consumer import event_consumer

async def test_producer():
    """Test producer connection"""
    print("=== Testing Producer Connection ===")
    try:
        await event_producer.connect()
        print("✅ Producer connected successfully")
        
        # Test health check
        health = await event_producer.health_check()
        print(f"📊 Health status: {health}")
        
        return True
    except Exception as e:
        print(f"❌ Producer connection failed: {e}")
        return False

async def test_consumer():
    """Test consumer connection"""
    print("\n=== Testing Consumer Connection ===")
    try:
        await event_consumer.connect()
        print("✅ Consumer connected successfully")
        
        # Test health check
        health = await event_consumer.health_check()
        print(f"📊 Health status: {health}")
        
        return True
    except Exception as e:
        print(f"❌ Consumer connection failed: {e}")
        return False

async def test_publish():
    """Test publishing a message"""
    print("\n=== Testing Event Publishing ===")
    try:
        from app.schemas.event import EventType
        
        # Test publishing with cross-service routing
        await event_producer.publish_event(
            EventType.PRODUCT_CREATED,
            {"product_id": "test-123", "sku": "TEST-SKU", "nom": "Test Product"},
            target_service="commandes"
        )
        print("✅ Event published successfully to commandes")
        
        await event_producer.publish_event(
            EventType.PRODUCT_CREATED,
            {"product_id": "test-123", "sku": "TEST-SKU", "nom": "Test Product"}
        )
        print("✅ General event published successfully")
        
        return True
    except Exception as e:
        print(f"❌ Publishing failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🔧 RabbitMQ Connection Test for Railway\n")
    
    # Display environment variables
    print("📋 Environment Variables:")
    for key in ["RABBITMQ_URL", "RABBITMQ_PRIVATE_URL", "RABBITMQ_HOST", "SERVICE_NAME"]:
        value = os.getenv(key, "not set")
        if "URL" in key and value != "not set":
            # Mask password
            if "@" in value:
                parts = value.split("@")
                value = f"{parts[0].split(':')[0]}:***@{parts[1]}"
        print(f"  {key}: {value}")
    print()
    
    results = []
    
    # Test producer
    results.append(await test_producer())
    
    # Test consumer
    results.append(await test_consumer())
    
    # Test publishing (only if connections succeeded)
    if all(results):
        results.append(await test_publish())
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        await event_producer.disconnect()
        await event_consumer.disconnect()
        print("✅ Cleanup complete")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    # Summary
    print("\n" + "="*50)
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
