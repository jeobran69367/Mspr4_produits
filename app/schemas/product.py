from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.product import ProductStatus


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    nom: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    categorie_id: UUID
    prix_ht: Decimal = Field(..., gt=0, decimal_places=2)
    taux_tva: Decimal = Field(default=20.0, ge=0, le=100, decimal_places=2)
    unite_mesure: str = Field(default="g", max_length=20)
    poids_unitaire: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    fournisseur: Optional[str] = Field(None, max_length=100)
    origine: Optional[str] = Field(None, max_length=100)
    notes_qualite: Optional[str] = None


class ProductCreate(ProductBase):
    @field_validator('prix_ht', 'taux_tva')
    @classmethod
    def validate_decimal(cls, v):
        return Decimal(str(v))


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    nom: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    categorie_id: Optional[UUID] = None
    prix_ht: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    taux_tva: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    unite_mesure: Optional[str] = Field(None, max_length=20)
    poids_unitaire: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    fournisseur: Optional[str] = Field(None, max_length=100)
    origine: Optional[str] = Field(None, max_length=100)
    notes_qualite: Optional[str] = None
    statut: Optional[ProductStatus] = None


class ProductResponse(ProductBase):
    id: UUID
    prix_ttc: Decimal
    statut: ProductStatus
    date_creation: datetime
    date_modification: datetime
    
    class Config:
        from_attributes = True
