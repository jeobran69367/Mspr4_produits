from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StockBase(BaseModel):
    produit_id: UUID
    quantite_disponible: int = Field(default=0, ge=0)
    quantite_reservee: int = Field(default=0, ge=0)
    quantite_minimum: int = Field(default=10, ge=0)
    quantite_maximum: int = Field(default=1000, ge=0)


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    quantite_disponible: Optional[int] = Field(None, ge=0)
    quantite_reservee: Optional[int] = Field(None, ge=0)
    quantite_minimum: Optional[int] = Field(None, ge=0)
    quantite_maximum: Optional[int] = Field(None, ge=0)


class StockAdjustment(BaseModel):
    quantite: int = Field(..., description="Quantité à ajouter (positif) ou retirer (négatif)")


class StockResponse(StockBase):
    id: UUID
    alerte_stock_bas: bool
    date_derniere_entree: Optional[datetime] = None
    date_derniere_sortie: Optional[datetime] = None
    date_modification: datetime

    class Config:
        from_attributes = True
