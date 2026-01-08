import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any
import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
import ssl

logger = logging.getLogger(__name__)

class RailwayRabbitMQFix:
    """FIX for Railway RabbitMQ connection issues"""
    
    def __init__(self):
        # Récupération DIRECTE des variables Railway
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")
        
        if not self.rabbitmq_url:
            # Fallback si RABBITMQ_URL n'existe pas
            self.host = os.getenv("RABBITMQ_HOST", "localhost")
            self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
            self.username = os.getenv("RABBITMQ_USERNAME", "guest")
            self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
            self.vhost = os.getenv("RABBITMQ_VHOST", "/")
            
            # Construction de l'URL
            self.rabbitmq_url = f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.vhost}"
        
        logger.info(f"RabbitMQ URL: {self.rabbitmq_url.replace(self.password, '***') if self.password else self.rabbitmq_url}")
        
        # Service config
        self.service_name = os.getenv("SERVICE_NAME", "unknown")
        self.exchange_name = "mspr.events"
        
        # Connection
        self.connection = None
        self.channel = None
        
    def _is_railway_ssl_url(self):
        """Check if URL uses SSL (Railway often does)"""
        return self.rabbitmq_url.startswith("amqps://")
    
    async def connect(self) -> bool:
        """Connect to Railway RabbitMQ with proper SSL handling"""
        try:
            logger.info("Attempting to connect to RabbitMQ...")
            
            # SSL context pour Railway
            ssl_context = None
            if self._is_railway_ssl_url():
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.info("Using SSL context for Railway")
            
            # IMPORTANT: Railway nécessite un timeout court
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                ssl_context=ssl_context,
                timeout=10,  # Railway timeout court
                heartbeat=30,  # Keepalive important
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=5)
            
            # Créer l'échange
            await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            
            logger.info("✅ SUCCESS: Connected to Railway RabbitMQ")
            return True
            
        except Exception as e:
            logger.error(f"❌ FAILED to connect: {type(e).__name__}: {e}")
            
            # Debug info
            logger.info("=== DEBUG INFO ===")
            logger.info(f"URL: {self.rabbitmq_url}")
            logger.info(f"SSL: {self._is_railway_ssl_url()}")
            logger.info(f"Service: {self.service_name}")
            
            return False
    
    async def test_publish(self):
        """Test publication d'un message"""
        try:
            exchange = await self.channel.get_exchange(self.exchange_name)
            
            message = Message(
                body=json.dumps({"test": True, "service": self.service_name}).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
            )
            
            await exchange.publish(
                message,
                routing_key=f"{self.service_name}.test"
            )
            
            logger.info("✅ Test message published")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish: {e}")
            return False
    
    async def test_consume(self):
        """Test consommation d'un message"""
        try:
            queue = await self.channel.declare_queue(
                f"{self.service_name}.test.queue",
                durable=True,
            )
            
            await queue.bind(self.exchange_name, routing_key=f"{self.service_name}.#")
            
            logger.info("✅ Queue declared and bound")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup consumer: {e}")
            return False

# Singleton
rabbitmq = RailwayRabbitMQFix()