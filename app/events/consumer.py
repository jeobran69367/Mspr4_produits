import json
import logging
import os
import ssl
import asyncio
from typing import Callable, Optional

import aio_pika
from aio_pika import ExchangeType, IncomingMessage

from app.config import settings

logger = logging.getLogger(__name__)


class EventConsumer:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self.queue: Optional[aio_pika.Queue] = None
        self._connecting = False
        
        # Determine RabbitMQ URL with Railway priority
        self.rabbitmq_url = self._get_rabbitmq_url()
        self.exchange_name = settings.RABBITMQ_EXCHANGE
        self.queue_name = settings.RABBITMQ_QUEUE_PRODUCTS
        self.service_name = settings.SERVICE_NAME
        
        logger.info(f"EventConsumer initialized for service: {self.service_name}")
        logger.info(f"Queue: {self.queue_name}")

    def _get_rabbitmq_url(self) -> str:
        """Get RabbitMQ URL with priority: PRIVATE_URL > URL > constructed from parts"""
        # 1. Priority: Railway private URL
        url = os.getenv("RABBITMQ_PRIVATE_URL")
        if url:
            logger.info("Using RABBITMQ_PRIVATE_URL")
            return url
        
        # 2. Fallback: Railway public URL
        url = os.getenv("RABBITMQ_URL") or settings.RABBITMQ_URL
        if url and url != "amqp://guest:guest@localhost:5672/":
            logger.info("Using RABBITMQ_URL")
            return url
        
        # 3. Fallback: Construct from settings (Railway may use DEFAULT_USER/PASS)
        username = os.getenv("RABBITMQ_DEFAULT_USER") or settings.RABBITMQ_USERNAME
        password = os.getenv("RABBITMQ_DEFAULT_PASS") or settings.RABBITMQ_PASSWORD
        host = settings.RABBITMQ_HOST
        port = settings.RABBITMQ_PORT
        vhost = settings.RABBITMQ_VHOST
        
        url = f"amqp://{username}:{password}@{host}:{port}{vhost}"
        logger.info("Using constructed URL from settings")
        return url

    def _get_ssl_context(self):
        """
        Get SSL context if URL uses amqps://
        
        Note: Railway's RabbitMQ service uses self-signed certificates,
        so we disable certificate verification. In production with proper
        certificates, enable verification by setting:
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        """
        if self.rabbitmq_url and self.rabbitmq_url.startswith("amqps://"):
            ssl_context = ssl.create_default_context()
            # Railway uses self-signed certs - disable verification
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
        return None

    async def connect(self):
        """Establish connection to RabbitMQ with retry logic"""
        if self._connecting:
            logger.info("Connection attempt already in progress")
            return
        
        if self.connection and not self.connection.is_closed:
            logger.info("Already connected to RabbitMQ")
            return
        
        self._connecting = True
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔗 Consumer connection attempt {attempt + 1}/{max_retries}")
                
                ssl_context = self._get_ssl_context()
                
                # Railway production connection with robust parameters
                self.connection = await aio_pika.connect_robust(
                    self.rabbitmq_url,
                    ssl_context=ssl_context,
                    timeout=10,
                    heartbeat=30,
                    client_properties={
                        "connection_name": f"{self.service_name}-consumer",
                        "product": "MSPR-Produits",
                        "platform": "Railway"
                    }
                )
                
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)

                self.exchange = await self.channel.declare_exchange(
                    self.exchange_name,
                    ExchangeType.TOPIC,
                    durable=True,
                    auto_delete=False
                )

                self.queue = await self.channel.declare_queue(
                    self.queue_name,
                    durable=True,
                    auto_delete=False,
                    arguments={
                        "x-max-length": 10000,
                        "x-message-ttl": 86400000,  # 24 hours
                    }
                )

                logger.info("✅ Consumer connected to RabbitMQ successfully")
                self._connecting = False
                return
                
            except aio_pika.exceptions.AMQPConnectionError as e:
                logger.error(f"❌ AMQP Connection Error (attempt {attempt + 1}): {e}")
                
            except Exception as e:
                logger.error(f"❌ Connection failed (attempt {attempt + 1}): {type(e).__name__}: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
        
        self._connecting = False
        logger.error("❌ All consumer connection attempts failed")
        raise ConnectionError("Failed to connect to RabbitMQ after all retries")

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Consumer disconnected from RabbitMQ")
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def bind_queue(self, routing_key: str):
        """Bind queue to exchange with routing key"""
        if not self.queue:
            await self.connect()
        
        await self.queue.bind(self.exchange, routing_key=routing_key)
        logger.info(f"Queue bound to routing key: {routing_key}")

    async def start_consuming(self, callback: Callable):
        """Start consuming messages from the queue"""
        if not self.queue:
            await self.connect()

        async def process_message(message: IncomingMessage):
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    logger.info(f"📥 Received message: {body.get('event_type', 'unknown')}")
                    await callback(body)
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")

        await self.queue.consume(process_message)
        logger.info("✅ Started consuming messages")

    async def health_check(self) -> dict:
        """Health check for RabbitMQ connection"""
        if not self.connection or self.connection.is_closed:
            return {
                "status": "disconnected",
                "service": self.service_name,
                "rabbitmq": "not_connected"
            }
        
        try:
            # Check if queue is available
            if self.queue:
                queue_info = await self.queue.declare(passive=True)
                return {
                    "status": "healthy",
                    "service": self.service_name,
                    "rabbitmq": "connected",
                    "queue": self.queue_name,
                    "message_count": queue_info.declaration_result.message_count
                }
            return {
                "status": "connected_no_queue",
                "service": self.service_name,
                "rabbitmq": "connected"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": self.service_name,
                "rabbitmq": "connection_error",
                "error": str(e)
            }


# Global event consumer instance
event_consumer = EventConsumer()
