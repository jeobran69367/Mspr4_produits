from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class EventType(str, Enum):
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    STOCK_UPDATED = "stock.updated"
    STOCK_LOW_ALERT = "stock.low_alert"


class Event(BaseModel):
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ProductEvent(BaseModel):
    product_id: UUID
    sku: str
    nom: str
    statut: str


class StockEvent(BaseModel):
    product_id: UUID
    quantite_disponible: int
    alerte_stock_bas: bool
