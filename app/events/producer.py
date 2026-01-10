import json
import logging
import os
import ssl
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode

from app.config import settings
from app.schemas.event import Event, EventType

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._connecting = False
        
        # Determine RabbitMQ URL with Railway priority
        self.rabbitmq_url = self._get_rabbitmq_url()
        self.exchange_name = settings.RABBITMQ_EXCHANGE
        self.service_name = settings.SERVICE_NAME
        
        logger.info(f"EventProducer initialized for service: {self.service_name}")
        logger.info(f"Exchange: {self.exchange_name}")

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
                logger.info(f"🔗 Connection attempt {attempt + 1}/{max_retries}")
                
                ssl_context = self._get_ssl_context()
                
                # Railway production connection with robust parameters
                self.connection = await aio_pika.connect_robust(
                    self.rabbitmq_url,
                    ssl_context=ssl_context,
                    timeout=10,
                    heartbeat=30,
                    client_properties={
                        "connection_name": f"{self.service_name}-producer",
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
                
                logger.info("✅ Connected to RabbitMQ successfully")
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
        logger.error("❌ All connection attempts failed")
        raise ConnectionError("Failed to connect to RabbitMQ after all retries")

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
        self.connection = None
        self.channel = None
        self.exchange = None

    async def publish_event(self, event_type: EventType, data: Dict[str, Any], target_service: str = None):
        """
        Publish an event to RabbitMQ with cross-service routing support
        
        Args:
            event_type: Type of event (e.g., EventType.PRODUCT_DELETED)
            data: Event data payload
            target_service: Optional target service (e.g., 'commandes', 'clients')
        """
        # Ensure connection
        if not self.exchange or not self.connection or self.connection.is_closed:
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Cannot publish event - connection failed: {e}")
                return

        event = Event(event_type=event_type, timestamp=datetime.utcnow(), data=data)
        message_body = json.dumps(event.model_dump(), default=str)

        try:
            # Determine routing key format
            # For cross-service: produits.deleted.commandes
            # For general: produits.deleted
            if target_service:
                routing_key = f"{self.service_name}.{event_type.value}.{target_service}"
            else:
                routing_key = f"{self.service_name}.{event_type.value}"
            
            message = Message(
                body=message_body.encode(),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "source_service": self.service_name,
                    "event_type": event_type.value,
                    "target_service": target_service or "all",
                }
            )
            
            await self.exchange.publish(message, routing_key=routing_key)
            logger.info(f"📤 Published event: {routing_key}")
            
        except aio_pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ Connection error while publishing: {e}")
            # Try to reconnect and retry once
            try:
                await self.connect()
                # Retry publish with same message and routing key
                await self.exchange.publish(message, routing_key=routing_key)
                logger.info(f"✅ Retry successful: {routing_key}")
            except Exception as retry_error:
                logger.error(f"❌ Retry failed: {retry_error}")
                raise
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            raise

    async def health_check(self) -> dict:
        """Health check for RabbitMQ connection"""
        if not self.connection or self.connection.is_closed:
            return {
                "status": "disconnected",
                "service": self.service_name,
                "rabbitmq": "not_connected"
            }
        
        try:
            # Test by declaring a temporary queue
            test_queue = await self.channel.declare_queue(
                f"health-check-{self.service_name}-producer",
                durable=False,
                auto_delete=True,
                exclusive=True
            )
            await test_queue.delete()
            
            return {
                "status": "healthy",
                "service": self.service_name,
                "rabbitmq": "connected",
                "exchange": self.exchange_name
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": self.service_name,
                "rabbitmq": "connection_error",
                "error": str(e)
            }


# Global event producer instance
event_producer = EventProducer()
