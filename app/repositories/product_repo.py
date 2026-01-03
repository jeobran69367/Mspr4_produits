from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from app.models.product import Product, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[ProductStatus] = None) -> List[Product]:
        query = self.db.query(Product)
        if status:
            query = query.filter(Product.statut == status)
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.db.query(Product).filter(Product.sku == sku).first()

    def get_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.db.query(Product).filter(Product.categorie_id == category_id).offset(skip).limit(limit).all()

    def create(self, product: ProductCreate) -> Product:
        # Calculate prix_ttc
        prix_ttc = Decimal(str(product.prix_ht)) * (1 + Decimal(str(product.taux_tva)) / 100)

        product_dict = product.model_dump()
        product_dict["prix_ttc"] = prix_ttc

        db_product = Product(**product_dict)
        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    def update(self, product_id: UUID, product_update: ProductUpdate) -> Optional[Product]:
        db_product = self.get_by_id(product_id)
        if db_product:
            update_data = product_update.model_dump(exclude_unset=True)

            # Recalculate prix_ttc if prix_ht or taux_tva changed
            if "prix_ht" in update_data or "taux_tva" in update_data:
                prix_ht = update_data.get("prix_ht", db_product.prix_ht)
                taux_tva = update_data.get("taux_tva", db_product.taux_tva)
                update_data["prix_ttc"] = Decimal(prix_ht) * (1 + Decimal(taux_tva) / 100)

            for field, value in update_data.items():
                setattr(db_product, field, value)

            self.db.commit()
            self.db.refresh(db_product)
        return db_product

    def delete(self, product_id: UUID) -> bool:
        db_product = self.get_by_id(product_id)
        if db_product:
            self.db.delete(db_product)
            self.db.commit()
            return True
        return False

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Product]:
        return (
            self.db.query(Product)
            .filter(Product.nom.ilike(f"%{query}%") | Product.description.ilike(f"%{query}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )
