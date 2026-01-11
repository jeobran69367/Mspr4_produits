import json
import logging
from datetime import datetime
from typing import Any, Dict
import asyncio

import aio_pika
from aio_pika import ExchangeType, Message

from app.config import settings, mask_url_password
from app.schemas.event import Event, EventType

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            # Use the correct URL with fallback logic (PRIVATE_URL -> URL -> constructed)
            rabbitmq_url = settings.get_rabbitmq_url()
            
            # Log which URL is being used (mask password for security)
            logger.info(f"Connecting to RabbitMQ using URL: {mask_url_password(rabbitmq_url)}")
            
            # Add timeout to prevent hanging during startup
            self.connection = await asyncio.wait_for(
                aio_pika.connect_robust(rabbitmq_url),
                timeout=10.0
            )
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE, ExchangeType.TOPIC, durable=True
            )
            logger.info("Connected to RabbitMQ")
        except asyncio.TimeoutError:
            logger.error("RabbitMQ connection timed out after 10 seconds")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish_event(self, event_type: EventType, data: Dict[str, Any], routing_key: str = "products"):
        """Publish an event to RabbitMQ"""
        if not self.exchange:
            await self.connect()

        event = Event(event_type=event_type, timestamp=datetime.utcnow(), data=data)

        message_body = json.dumps(event.model_dump(), default=str)

        try:
            await self.exchange.publish(
                Message(
                    body=message_body.encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=f"{routing_key}.{event_type.value}",
            )
            logger.info(f"Published event: {event_type.value}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise


# Global event producer instance
event_producer = EventProducer()
