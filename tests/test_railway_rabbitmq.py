#!/usr/bin/env python3
"""
URGENT: Test RabbitMQ connection on Railway
"""

import os
import sys
import asyncio
import aio_pika
import ssl

async def test():
    print("=== RAILWAY RABBITMQ CONNECTION TEST ===\n")
    
    # Get ALL environment variables
    env_vars = {
        'RABBITMQ_URL': os.getenv('RABBITMQ_URL'),
        'RABBITMQ_HOST': os.getenv('RABBITMQ_HOST'),
        'RABBITMQ_PORT': os.getenv('RABBITMQ_PORT'),
        'RABBITMQ_USERNAME': os.getenv('RABBITMQ_USERNAME'),
        'RABBITMQ_PASSWORD': os.getenv('RABBITMQ_PASSWORD'),
        'RABBITMQ_PRIVATE_URL': os.getenv('RABBITMQ_PRIVATE_URL'),
        'SERVICE_NAME': os.getenv('SERVICE_NAME'),
    }
    
    print("📋 Environment Variables:")
    for key, value in env_vars.items():
        if value and 'PASSWORD' in key:
            print(f"  {key}: {'*' * 8}")
        else:
            print(f"  {key}: {value}")
    
    print("\n🔗 Testing connection...")
    
    # Determine which URL to use
    rabbitmq_url = env_vars['RABBITMQ_URL']
    
    if not rabbitmq_url and env_vars['RABBITMQ_HOST']:
        # Construct URL from parts
        rabbitmq_url = f"amqp://{env_vars['RABBITMQ_USERNAME']}:{env_vars['RABBITMQ_PASSWORD']}@{env_vars['RABBITMQ_HOST']}:{env_vars['RABBITMQ_PORT'] or '5672'}/"
    
    if not rabbitmq_url:
        print("❌ ERROR: No RabbitMQ URL found!")
        print("Please set RABBITMQ_URL or RABBITMQ_HOST variables")
        return False
    
    print(f"📡 Using URL: {rabbitmq_url.replace(env_vars.get('RABBITMQ_PASSWORD', ''), '***')}")
    
    try:
        # Try with SSL first (Railway usually uses amqps://)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        print("🔐 Attempting SSL connection...")
        connection = await aio_pika.connect_robust(
            rabbitmq_url,
            ssl_context=ssl_context,
            timeout=10
        )
        
        print("✅ SSL Connection successful!")
        
        # Test channel
        channel = await connection.channel()
        print("✅ Channel created")
        
        # Test exchange
        exchange = await channel.declare_exchange(
            "test.exchange",
            aio_pika.ExchangeType.TOPIC,
            durable=False,
            auto_delete=True
        )
        print("✅ Exchange declared")
        
        # Test publish
        await exchange.publish(
            aio_pika.Message(b"Test message from Railway"),
            routing_key="test.key"
        )
        print("✅ Message published")
        
        await connection.close()
        print("\n🎉 ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ SSL Connection failed: {type(e).__name__}: {e}")
        
        # Try without SSL
        try:
            print("\n🔓 Attempting non-SSL connection...")
            
            # Replace amqps:// with amqp://
            non_ssl_url = rabbitmq_url.replace("amqps://", "amqp://")
            
            connection = await aio_pika.connect_robust(
                non_ssl_url,
                timeout=10
            )
            
            print("✅ Non-SSL Connection successful!")
            await connection.close()
            return True
            
        except Exception as e2:
            print(f"❌ Non-SSL also failed: {type(e2).__name__}: {e2}")
            return False

async def main():
    success = await test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())