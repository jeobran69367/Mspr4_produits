from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from app.database import get_db
from app.services.stock_service import StockService
from app.schemas.stock import StockCreate, StockUpdate, StockResponse, StockAdjustment
from app.events.producer import event_producer
from app.schemas.event import EventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/", response_model=List[StockResponse])
def get_all_stocks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all stock entries"""
    service = StockService(db)
    return service.get_all_stocks(skip, limit)


@router.get("/alerts", response_model=List[StockResponse])
def get_low_stock_alerts(db: Session = Depends(get_db)):
    """Get products with low stock alerts"""
    service = StockService(db)
    return service.get_low_stock_alerts()


@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(stock_id: UUID, db: Session = Depends(get_db)):
    """Get a specific stock entry by ID"""
    service = StockService(db)
    stock = service.get_stock(stock_id)
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock with id {stock_id} not found")
    return stock


@router.get("/product/{product_id}", response_model=StockResponse)
def get_stock_by_product(product_id: UUID, db: Session = Depends(get_db)):
    """Get stock for a specific product"""
    service = StockService(db)
    stock = service.get_stock_by_product(product_id)
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock for product {product_id} not found")
    return stock


@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(stock: StockCreate, db: Session = Depends(get_db)):
    """Create a new stock entry"""
    service = StockService(db)
    try:
        return service.create_stock(stock)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{stock_id}", response_model=StockResponse)
async def update_stock(stock_id: UUID, stock_update: StockUpdate, db: Session = Depends(get_db)):
    """Update a stock entry"""
    service = StockService(db)
    updated_stock = service.update_stock(stock_id, stock_update)
    if not updated_stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock with id {stock_id} not found")

    # Publish event
    try:
        await event_producer.publish_event(
            EventType.STOCK_UPDATED,
            {
                "product_id": str(updated_stock.produit_id),
                "quantite_disponible": updated_stock.quantite_disponible,
                "alerte_stock_bas": updated_stock.alerte_stock_bas,
            },
        )

        # Publish low stock alert if needed
        if updated_stock.alerte_stock_bas:
            await event_producer.publish_event(
                EventType.STOCK_LOW_ALERT,
                {
                    "product_id": str(updated_stock.produit_id),
                    "quantite_disponible": updated_stock.quantite_disponible,
                    "quantite_minimum": updated_stock.quantite_minimum,
                },
            )
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

    return updated_stock


@router.post("/product/{product_id}/adjust", response_model=StockResponse)
async def adjust_stock(product_id: UUID, adjustment: StockAdjustment, db: Session = Depends(get_db)):
    """Adjust stock quantity for a product (add or remove)"""
    service = StockService(db)
    try:
        updated_stock = service.adjust_stock(product_id, adjustment.quantite)
        if not updated_stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock for product {product_id} not found"
            )

        # Publish event
        try:
            await event_producer.publish_event(
                EventType.STOCK_UPDATED,
                {
                    "product_id": str(updated_stock.produit_id),
                    "quantite_disponible": updated_stock.quantite_disponible,
                    "alerte_stock_bas": updated_stock.alerte_stock_bas,
                    "adjustment": adjustment.quantite,
                },
            )

            # Publish low stock alert if needed
            if updated_stock.alerte_stock_bas:
                await event_producer.publish_event(
                    EventType.STOCK_LOW_ALERT,
                    {
                        "product_id": str(updated_stock.produit_id),
                        "quantite_disponible": updated_stock.quantite_disponible,
                        "quantite_minimum": updated_stock.quantite_minimum,
                    },
                )
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

        return updated_stock
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(stock_id: UUID, db: Session = Depends(get_db)):
    """Delete a stock entry"""
    service = StockService(db)
    if not service.delete_stock(stock_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock with id {stock_id} not found")
    return None
