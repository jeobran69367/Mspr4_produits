from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.models.product import ProductStatus
from app.events.producer import event_producer
from app.schemas.event import EventType

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ProductStatus] = None,
    category_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering"""
    service = ProductService(db)
    
    if search:
        return service.search_products(search, skip, limit)
    elif category_id:
        return service.get_products_by_category(category_id, skip, limit)
    else:
        return service.get_products(skip, limit, status)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific product by ID"""
    service = ProductService(db)
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product"""
    service = ProductService(db)
    try:
        created_product = service.create_product(product)
        
        # Publish event
        try:
            await event_producer.publish_event(
                EventType.PRODUCT_CREATED,
                {
                    "product_id": str(created_product.id),
                    "sku": created_product.sku,
                    "nom": created_product.nom,
                    "statut": created_product.statut.value
                }
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to publish event: {e}")
        
        return created_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product"""
    service = ProductService(db)
    try:
        updated_product = service.update_product(product_id, product_update)
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        
        # Publish event
        try:
            await event_producer.publish_event(
                EventType.PRODUCT_UPDATED,
                {
                    "product_id": str(updated_product.id),
                    "sku": updated_product.sku,
                    "nom": updated_product.nom,
                    "statut": updated_product.statut.value
                }
            )
        except Exception as e:
            print(f"Failed to publish event: {e}")
        
        return updated_product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a product"""
    service = ProductService(db)
    
    # Get product details before deleting
    product = service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    if not service.delete_product(product_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Publish event
    try:
        await event_producer.publish_event(
            EventType.PRODUCT_DELETED,
            {
                "product_id": str(product_id),
                "sku": product.sku
            }
        )
    except Exception as e:
        print(f"Failed to publish event: {e}")
    
    return None
