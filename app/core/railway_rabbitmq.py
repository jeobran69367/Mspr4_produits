import os
import json
import logging
import asyncio
import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
from typing import Optional
import ssl

logger = logging.getLogger(__name__)

class RailwayRabbitMQ:
    """RabbitMQ client for Railway PRODUCTION"""
    
    def __init__(self):
        # 1. PRIORITÉ: URL privée Railway
        self.rabbitmq_url = os.getenv("RABBITMQ_PRIVATE_URL")
        
        # 2. Fallback: URL publique Railway
        if not self.rabbitmq_url:
            self.rabbitmq_url = os.getenv("RABBITMQ_URL")
        
        # 3. Fallback: Construire à partir des variables d'environnement
        if not self.rabbitmq_url:
            host = os.getenv("RABBITMQ_HOST", "rabbitmq")
            port = os.getenv("RABBITMQ_PORT", "5672")
            username = os.getenv("RABBITMQ_USERNAME", "guest")
            password = os.getenv("RABBITMQ_PASSWORD", "guest")
            vhost = os.getenv("RABBITMQ_VHOST", "/")
            
            self.rabbitmq_url = f"amqp://{username}:{password}@{host}:{port}/{vhost}"
        
        self.service_name = os.getenv("SERVICE_NAME", "produits")
        self.exchange_name = os.getenv("RABBITMQ_EXCHANGE", "mspr.events")
        
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        
        logger.info(f"🔧 Initializing RabbitMQ for {self.service_name}")
        logger.info(f"📡 URL: {self._mask_url(self.rabbitmq_url)}")
        logger.info(f"🏷️  Service: {self.service_name}")
        logger.info(f"📊 Exchange: {self.exchange_name}")
    
    def _mask_url(self, url: str) -> str:
        """Mask password in logs"""
        if url and "@" in url:
            parts = url.split("@")
            cred_part = parts[0]
            if ":" in cred_part:
                cred_part = cred_part.split(":")[0] + ":***"
            return f"{cred_part}@{parts[1]}"
        return url or "not set"
    
    def _get_ssl_context(self):
        """Get SSL context if URL uses amqps://"""
        if self.rabbitmq_url and self.rabbitmq_url.startswith("amqps://"):
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        return None
    
    async def connect(self) -> bool:
        """Connect to RabbitMQ with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔗 Connection attempt {attempt + 1}/{max_retries}")
                
                if not self.rabbitmq_url:
                    logger.error("❌ No RabbitMQ URL configured")
                    return False
                
                ssl_context = self._get_ssl_context()
                
                # Railway PRODUCTION connection parameters
                self.connection = await aio_pika.connect_robust(
                    self.rabbitmq_url,
                    ssl_context=ssl_context,
                    timeout=10,  # Timeout court pour Railway
                    heartbeat=30,  # Keepalive important
                    client_properties={
                        "connection_name": f"{self.service_name}-service",
                        "product": "MSPR-Produits",
                        "platform": "Railway"
                    }
                )
                
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)
                
                logger.info("✅ Connected to RabbitMQ")
                return True
                
            except aio_pika.exceptions.AMQPConnectionError as e:
                logger.error(f"❌ AMQP Connection Error (attempt {attempt + 1}): {e}")
                
            except Exception as e:
                logger.error(f"❌ Connection failed (attempt {attempt + 1}): {type(e).__name__}: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
        
        logger.error("❌ All connection attempts failed")
        return False
    
    async def setup(self):
        """Setup exchange and queue for this service"""
        try:
            # Declare exchange
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
                    "x-max-length": 10000,
                    "x-message-ttl": 86400000,  # 24 hours
                }
            )
            
            # Bind queue to exchange
            await queue.bind(exchange, routing_key=f"{self.service_name}.#")
            
            # Bind to other services for cross-communication
            if self.service_name == "produits":
                await queue.bind(exchange, routing_key="commandes.#")
                await queue.bind(exchange, routing_key="clients.#")
            
            logger.info(f"✅ Setup complete: {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def publish(self, event_type: str, data: dict, target_service: str = None):
        """Publish an event"""
        try:
            exchange = await self.channel.get_exchange(self.exchange_name)
            
            # Determine routing key
            if target_service:
                routing_key = f"{target_service}.{event_type}"
            else:
                routing_key = f"{self.service_name}.{event_type}"
            
            message = Message(
                body=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
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
    
    async def health_check(self) -> dict:
        """Health check for Railway"""
        if not self.connection or self.connection.is_closed:
            return {
                "status": "disconnected",
                "service": self.service_name,
                "rabbitmq": "not_connected"
            }
        
        try:
            # Test by declaring a temporary queue
            test_queue = await self.channel.declare_queue(
                f"health-check-{self.service_name}",
                durable=False,
                auto_delete=True
            )
            await test_queue.delete()
            
            return {
                "status": "healthy",
                "service": self.service_name,
                "rabbitmq": "connected",
                "url_used": self._mask_url(self.rabbitmq_url)
            }
            
        except Exception:
            return {
                "status": "unhealthy",
                "service": self.service_name,
                "rabbitmq": "connection_error"
            }
    
    async def close(self):
        """Close connection gracefully"""
        if self.connection:
            await self.connection.close()
            logger.info("Connection closed")

# Singleton instance
rabbitmq = RailwayRabbitMQ()