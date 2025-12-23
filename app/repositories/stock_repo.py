from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockUpdate


class StockRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Stock]:
        return self.db.query(Stock).offset(skip).limit(limit).all()
    
    def get_by_id(self, stock_id: UUID) -> Optional[Stock]:
        return self.db.query(Stock).filter(Stock.id == stock_id).first()
    
    def get_by_product(self, product_id: UUID) -> Optional[Stock]:
        return self.db.query(Stock).filter(Stock.produit_id == product_id).first()
    
    def get_low_stock(self) -> List[Stock]:
        return self.db.query(Stock).filter(Stock.alerte_stock_bas == True).all()
    
    def create(self, stock: StockCreate) -> Stock:
        db_stock = Stock(**stock.model_dump())
        # Check if stock is low
        db_stock.alerte_stock_bas = db_stock.quantite_disponible < db_stock.quantite_minimum
        self.db.add(db_stock)
        self.db.commit()
        self.db.refresh(db_stock)
        return db_stock
    
    def update(self, stock_id: UUID, stock_update: StockUpdate) -> Optional[Stock]:
        db_stock = self.get_by_id(stock_id)
        if db_stock:
            update_data = stock_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_stock, field, value)
            
            # Update alert status
            db_stock.alerte_stock_bas = db_stock.quantite_disponible < db_stock.quantite_minimum
            
            self.db.commit()
            self.db.refresh(db_stock)
        return db_stock
    
    def adjust_quantity(self, product_id: UUID, quantity_change: int) -> Optional[Stock]:
        db_stock = self.get_by_product(product_id)
        if db_stock:
            # Validate that stock won't go negative
            new_quantity = db_stock.quantite_disponible + quantity_change
            if new_quantity < 0:
                raise ValueError("Stock quantity cannot be negative")
            
            db_stock.quantite_disponible = new_quantity
            
            # Update timestamps based on operation type
            if quantity_change > 0:
                db_stock.date_derniere_entree = datetime.utcnow()
            elif quantity_change < 0:
                db_stock.date_derniere_sortie = datetime.utcnow()
            
            # Update alert status
            db_stock.alerte_stock_bas = db_stock.quantite_disponible < db_stock.quantite_minimum
            
            self.db.commit()
            self.db.refresh(db_stock)
        return db_stock
    
    def delete(self, stock_id: UUID) -> bool:
        db_stock = self.get_by_id(stock_id)
        if db_stock:
            self.db.delete(db_stock)
            self.db.commit()
            return True
        return False
