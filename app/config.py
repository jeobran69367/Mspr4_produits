from pydantic_settings import BaseSettings
from typing import Optional
import logging
import re
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def mask_url_password(url: str) -> str:
    """
    Mask password in URL for secure logging.
    Example: amqp://user:password@host:5672/ -> amqp://user:***@host:5672/
    """
    if not url:
        return url
    
    # Use regex to find and replace password in URL
    # Pattern matches: protocol://user:password@host
    pattern = r'(://[^:]+:)[^@]+(@)'
    masked = re.sub(pattern, r'\1***\2', url)
    return masked


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/produits_db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "produits_db"

    # RabbitMQ - FOR RAILWAY PRODUCTION
    RABBITMQ_URL: Optional[str] = None  # Laisser None pour utiliser l'URL Railway
    RABBITMQ_PRIVATE_URL: Optional[str] = None  # URL interne Railway
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USERNAME: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    # Exchange and Queue names
    RABBITMQ_EXCHANGE: str = "mspr.events"
    RABBITMQ_QUEUE_PRODUCTS: str = "produits.queue"

    # Service identification
    SERVICE_NAME: str = "produits"

    # Application
    APP_NAME: str = "Service Produits - PayeTonKawa"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # False en production
    API_V1_PREFIX: str = "/api/v1"
    TESTING: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_rabbitmq_url(self) -> str:
        """
        Get RabbitMQ URL with proper fallback logic for Railway production.
        Priority: RABBITMQ_PRIVATE_URL -> RABBITMQ_URL -> constructed from components
        """
        # 1. Priority: Railway private URL (internal network)
        if self.RABBITMQ_PRIVATE_URL:
            logger.info("Using RABBITMQ_PRIVATE_URL for connection")
            return self.RABBITMQ_PRIVATE_URL
        
        # 2. Fallback: Railway public URL
        if self.RABBITMQ_URL:
            logger.info("Using RABBITMQ_URL for connection")
            return self.RABBITMQ_URL
        
        # 3. Fallback: Construct from environment variables
        logger.info("Constructing RabbitMQ URL from individual components")
        # URL-encode credentials to handle special characters safely
        username = quote_plus(self.RABBITMQ_USERNAME)
        password = quote_plus(self.RABBITMQ_PASSWORD)
        vhost = quote_plus(self.RABBITMQ_VHOST) if self.RABBITMQ_VHOST != "/" else "/"
        return f"amqp://{username}:{password}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{vhost}"


settings = Settings()