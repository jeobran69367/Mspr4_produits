from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from alembic import command
from alembic.config import Config

from app.config import settings
from app.api.v1 import api_router
from app.events.producer import event_producer


# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Database migrations
# ------------------------------------------------------------------------------
def run_migrations():
    """
    Run Alembic migrations on startup.
    Required for Railway / production deployments.
    """
    try:
        logger.info("Running database migrations...")
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            settings.DATABASE_URL
        )
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise


# ------------------------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting application...")

    # 1️⃣ Migrations DB
    run_migrations()

    # 2️⃣ RabbitMQ
    try:
        await event_producer.connect()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.warning(f"Failed to connect to RabbitMQ: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        await event_producer.disconnect()
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.warning(f"Error closing RabbitMQ connection: {e}")


# ------------------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST pour la gestion du catalogue de produits café",
    lifespan=lifespan,
)


# ------------------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ à restreindre en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "message": "Service Produits - PayeTonKawa",
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "products",
    }


# ------------------------------------------------------------------------------
# Local dev entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
