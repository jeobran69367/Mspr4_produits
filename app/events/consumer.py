import json
import logging
from typing import Callable

import aio_pika
from aio_pika import ExchangeType, IncomingMessage

from app.config import settings, mask_url_password

logger = logging.getLogger(__name__)


class EventConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            # Use the correct URL with fallback logic (PRIVATE_URL -> URL -> constructed)
            rabbitmq_url = settings.get_rabbitmq_url()
            
            # Log which URL is being used (mask password for security)
            logger.info(f"Consumer connecting to RabbitMQ using URL: {mask_url_password(rabbitmq_url)}")
            
            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE, ExchangeType.TOPIC, durable=True
            )

            self.queue = await self.channel.declare_queue(settings.RABBITMQ_QUEUE_PRODUCTS, durable=True)

            logger.info("Consumer connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect consumer to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Consumer disconnected from RabbitMQ")

    async def bind_queue(self, routing_key: str):
        """Bind queue to exchange with routing key"""
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
                    logger.info(f"Received message: {body}")
                    await callback(body)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        await self.queue.consume(process_message)
        logger.info("Started consuming messages")


# Global event consumer instance
event_consumer = EventConsumer()
