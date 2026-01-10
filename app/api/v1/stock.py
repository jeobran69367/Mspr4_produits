import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.producer import event_producer
from app.schemas.event import EventType
from app.schemas.stock import StockAdjustment, StockCreate, StockResponse, StockUpdate
from app.services.stock_service import StockService

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

    # Publish event to all services
    try:
        event_data = {
            "product_id": str(updated_stock.produit_id),
            "quantite_disponible": updated_stock.quantite_disponible,
            "alerte_stock_bas": updated_stock.alerte_stock_bas,
        }
        
        # Publish general event
        await event_producer.publish_event(
            EventType.STOCK_UPDATED,
            event_data,
        )
        
        # Publish to commandes service (important for order processing)
        await event_producer.publish_event(
            EventType.STOCK_UPDATED,
            event_data,
            target_service="commandes"
        )

        # Publish low stock alert if needed
        if updated_stock.alerte_stock_bas:
            alert_data = {
                "product_id": str(updated_stock.produit_id),
                "quantite_disponible": updated_stock.quantite_disponible,
                "quantite_minimum": updated_stock.quantite_minimum,
            }
            await event_producer.publish_event(
                EventType.STOCK_LOW_ALERT,
                alert_data,
            )
            # Also send to commandes
            await event_producer.publish_event(
                EventType.STOCK_LOW_ALERT,
                alert_data,
                target_service="commandes"
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

        # Publish event to all services
        try:
            event_data = {
                "product_id": str(updated_stock.produit_id),
                "quantite_disponible": updated_stock.quantite_disponible,
                "alerte_stock_bas": updated_stock.alerte_stock_bas,
                "adjustment": adjustment.quantite,
            }
            
            # Publish general event
            await event_producer.publish_event(
                EventType.STOCK_UPDATED,
                event_data,
            )
            
            # Publish to commandes service (important for order processing)
            await event_producer.publish_event(
                EventType.STOCK_UPDATED,
                event_data,
                target_service="commandes"
            )

            # Publish low stock alert if needed
            if updated_stock.alerte_stock_bas:
                alert_data = {
                    "product_id": str(updated_stock.produit_id),
                    "quantite_disponible": updated_stock.quantite_disponible,
                    "quantite_minimum": updated_stock.quantite_minimum,
                }
                await event_producer.publish_event(
                    EventType.STOCK_LOW_ALERT,
                    alert_data,
                )
                # Also send to commandes
                await event_producer.publish_event(
                    EventType.STOCK_LOW_ALERT,
                    alert_data,
                    target_service="commandes"
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
