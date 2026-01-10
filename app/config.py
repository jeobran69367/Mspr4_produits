from pydantic_settings import BaseSettings
from typing import Optional


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
    RABBITMQ_DEFAULT_USER: Optional[str] = None  # Railway variable
    RABBITMQ_DEFAULT_PASS: Optional[str] = None  # Railway variable
    RABBITMQ_NODENAME: Optional[str] = None  # Railway variable (info only)
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


settings = Settings()