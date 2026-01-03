from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.stock_repo import StockRepository
from app.schemas.stock import StockCreate, StockResponse, StockUpdate


class StockService:
    def __init__(self, db: Session):
        self.repository = StockRepository(db)

    def get_all_stocks(self, skip: int = 0, limit: int = 100) -> List[StockResponse]:
        stocks = self.repository.get_all(skip, limit)
        return [StockResponse.model_validate(stock) for stock in stocks]

    def get_stock(self, stock_id: UUID) -> Optional[StockResponse]:
        stock = self.repository.get_by_id(stock_id)
        return StockResponse.model_validate(stock) if stock else None

    def get_stock_by_product(self, product_id: UUID) -> Optional[StockResponse]:
        stock = self.repository.get_by_product(product_id)
        return StockResponse.model_validate(stock) if stock else None

    def get_low_stock_alerts(self) -> List[StockResponse]:
        stocks = self.repository.get_low_stock()
        return [StockResponse.model_validate(stock) for stock in stocks]

    def create_stock(self, stock: StockCreate) -> StockResponse:
        # Check if stock already exists for this product
        existing = self.repository.get_by_product(stock.produit_id)
        if existing:
            raise ValueError(f"Stock already exists for product {stock.produit_id}")

        db_stock = self.repository.create(stock)
        return StockResponse.model_validate(db_stock)

    def update_stock(self, stock_id: UUID, stock_update: StockUpdate) -> Optional[StockResponse]:
        updated_stock = self.repository.update(stock_id, stock_update)
        return StockResponse.model_validate(updated_stock) if updated_stock else None

    def adjust_stock(self, product_id: UUID, quantity_change: int) -> Optional[StockResponse]:
        """
        Adjust stock quantity by adding or removing items
        Positive quantity_change = stock entry
        Negative quantity_change = stock exit
        """
        stock = self.repository.adjust_quantity(product_id, quantity_change)
        return StockResponse.model_validate(stock) if stock else None

    def delete_stock(self, stock_id: UUID) -> bool:
        return self.repository.delete(stock_id)
