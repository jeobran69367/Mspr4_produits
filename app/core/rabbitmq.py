import os
import json
import logging
import asyncio
import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
import ssl

logger = logging.getLogger(__name__)

class RailwayRabbitMQ:
    """RabbitMQ client optimized for Railway internal network"""
    
    def __init__(self):
        # Get Railway environment variables
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")
        
        # Fallback to private URL if available
        if not self.rabbitmq_url:
            self.rabbitmq_url = os.getenv("RABBITMQ_PRIVATE_URL")
        
        if not self.rabbitmq_url:
            # Construct from parts
            host = os.getenv("RABBITMQ_HOST", "rabbitmq-production-88b6.railway.internal")
            port = os.getenv("RABBITMQ_PORT", "5672")
            username = os.getenv("RABBITMQ_USERNAME", "fxVv7KIxHFdLGACv")
            password = os.getenv("RABBITMQ_PASSWORD", "s6LXsqKWyqV.KWtR~BYGUnxfgUid6AAq")
            vhost = os.getenv("RABBITMQ_VHOST", "/")
            
            self.rabbitmq_url = f"amqp://{username}:{password}@{host}:{port}/{vhost}"
        
        self.service_name = os.getenv("SERVICE_NAME", "unknown")
        self.exchange_name = "mspr.events"
        
        self.connection = None
        self.channel = None
        
        logger.info(f"Initializing RabbitMQ for {self.service_name}")
        logger.info(f"Using URL: {self._mask_url()}")
    
    def _mask_url(self):
        """Mask password in logs"""
        if "@" in self.rabbitmq_url:
            parts = self.rabbitmq_url.split("@")
            cred_part = parts[0]
            if ":" in cred_part:
                cred_part = cred_part.split(":")[0] + ":***"
            return f"{cred_part}@{parts[1]}"
        return self.rabbitmq_url
    
    def _is_ssl_url(self):
        """Check if URL uses SSL"""
        return self.rabbitmq_url.startswith("amqps://")
    
    async def connect(self):
        """Connect to RabbitMQ on Railway internal network"""
        try:
            logger.info("🔗 Connecting to Railway RabbitMQ...")
            
            # For Railway INTERNAL network, NO SSL needed
            ssl_context = None
            if self._is_ssl_url():
                # Only use SSL if explicitly using amqps://
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.info("Using SSL context")
            else:
                logger.info("Using plain AMQP (no SSL) for internal network")
            
            # IMPORTANT: Railway internal network has different timeouts
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                ssl_context=ssl_context,
                timeout=15,  # Increased timeout for internal network
                heartbeat=60,  # Keep connection alive
                client_properties={
                    "connection_name": f"{self.service_name}-service",
                    "product": "MSPR-Microservices",
                }
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=20)
            
            logger.info("✅ Connected to RabbitMQ on Railway internal network")
            return True
            
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ AMQP Connection Error: {e}")
            
            # Diagnostic info
            logger.info("=== DIAGNOSTIC ===")
            logger.info(f"URL starts with amqps: {self._is_ssl_url()}")
            logger.info(f"Host in URL: {'@' in self.rabbitmq_url and self.rabbitmq_url.split('@')[1].split(':')[0]}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {type(e).__name__}: {e}")
            return False
    
    async def setup_infrastructure(self):
        """Setup exchange, queues and bindings"""
        try:
            # Declare main exchange
            exchange = await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True,
                auto_delete=False,
            )
            
            # Service-specific queue
            queue_name = f"{self.service_name}.queue"
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                auto_delete=False,
                arguments={
                    "x-dead-letter-exchange": f"{self.exchange_name}.dlx",
                    "x-max-length": 10000,
                    "x-message-ttl": 86400000,  # 24h
                }
            )
            
            # Bind queue to exchange with service routing key
            await queue.bind(exchange, routing_key=f"{self.service_name}.#")
            
            # Bind for cross-service communication
            if self.service_name == "commandes":
                await queue.bind(exchange, routing_key="produits.#")
                await queue.bind(exchange, routing_key="clients.#")
            elif self.service_name == "produits":
                await queue.bind(exchange, routing_key="commandes.#")
                await queue.bind(exchange, routing_key="clients.#")
            elif self.service_name == "clients":
                await queue.bind(exchange, routing_key="commandes.#")
                await queue.bind(exchange, routing_key="produits.#")
            
            logger.info(f"✅ Infrastructure setup: {queue_name}")
            return exchange, queue
            
        except Exception as e:
            logger.error(f"❌ Infrastructure setup failed: {e}")
            return None, None
    
    async def publish(self, event_type: str, data: dict, target_service: str = None):
        """Publish an event"""
        try:
            exchange = await self.channel.get_exchange(self.exchange_name)
            
            routing_key = f"{self.service_name}.{event_type}"
            if target_service:
                routing_key = f"{target_service}.{event_type}"
            
            message = Message(
                body=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="utf-8",
                headers={
                    "source_service": self.service_name,
                    "event_type": event_type,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )
            
            await exchange.publish(message, routing_key=routing_key)
            
            logger.info(f"📤 Published: {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Publish failed: {e}")
            return False
    
    async def consume(self, message_handler):
        """Start consuming messages"""
        try:
            queue_name = f"{self.service_name}.queue"
            queue = await self.channel.get_queue(queue_name)
            
            if not queue:
                logger.error(f"Queue {queue_name} not found")
                return
            
            async def process_message(message):
                async with message.process():
                    try:
                        body_str = message.body.decode('utf-8')
                        body = json.loads(body_str)
                        
                        logger.info(f"📩 Received: {message.routing_key}")
                        
                        # Call handler
                        await message_handler(
                            routing_key=message.routing_key,
                            body=body,
                            headers=message.headers or {}
                        )
                        
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in message: {message.body}")
                        await message.nack(requeue=False)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await message.nack(requeue=True)
            
            await queue.consume(process_message)
            logger.info(f"📥 Started consuming from {queue_name}")
            
            # Keep consuming
            await asyncio.Future()  # Run forever
            
        except Exception as e:
            logger.error(f"❌ Consume failed: {e}")
            raise
    
    async def test_connection(self):
        """Test the complete setup"""
        try:
            # Test 1: Connection
            if not self.connection:
                return False
            
            # Test 2: Publish test message
            test_data = {
                "test": True,
                "service": self.service_name,
                "timestamp": asyncio.get_event_loop().time(),
            }
            
            await self.publish("connection_test", test_data)
            
            # Test 3: Verify queue exists
            queue_name = f"{self.service_name}.queue"
            queue = await self.channel.get_queue(queue_name)
            
            if queue:
                logger.info("✅ All connection tests passed")
                return True
            else:
                logger.error("❌ Queue not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
    
    async def close(self):
        """Close connection gracefully"""
        if self.connection:
            await self.connection.close()
            logger.info("Connection closed")

# Global instance
rabbitmq = RailwayRabbitMQ()