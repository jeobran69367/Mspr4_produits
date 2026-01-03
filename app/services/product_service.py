from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.product import ProductStatus
from app.repositories.product_repo import ProductRepository
from app.repositories.stock_repo import StockRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.stock import StockCreate


class ProductService:
    def __init__(self, db: Session):
        self.repository = ProductRepository(db)
        self.stock_repository = StockRepository(db)
        self.db = db

    def get_products(
        self, skip: int = 0, limit: int = 100, status: Optional[ProductStatus] = None
    ) -> List[ProductResponse]:
        products = self.repository.get_all(skip, limit, status)
        return [ProductResponse.model_validate(prod) for prod in products]

    def get_product(self, product_id: UUID) -> Optional[ProductResponse]:
        product = self.repository.get_by_id(product_id)
        return ProductResponse.model_validate(product) if product else None

    def get_products_by_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[ProductResponse]:
        products = self.repository.get_by_category(category_id, skip, limit)
        return [ProductResponse.model_validate(prod) for prod in products]

    def create_product(self, product: ProductCreate) -> ProductResponse:
        # Check if product with same SKU exists
        existing = self.repository.get_by_sku(product.sku)
        if existing:
            raise ValueError(f"Product with SKU '{product.sku}' already exists")

        # Create product
        db_product = self.repository.create(product)

        # Create initial stock entry
        stock = StockCreate(produit_id=db_product.id, quantite_disponible=0, quantite_reservee=0)
        self.stock_repository.create(stock)

        return ProductResponse.model_validate(db_product)

    def update_product(self, product_id: UUID, product_update: ProductUpdate) -> Optional[ProductResponse]:
        # If SKU is being updated, check it doesn't conflict
        if product_update.sku:
            existing = self.repository.get_by_sku(product_update.sku)
            if existing and existing.id != product_id:
                raise ValueError(f"Product with SKU '{product_update.sku}' already exists")

        updated_product = self.repository.update(product_id, product_update)
        return ProductResponse.model_validate(updated_product) if updated_product else None

    def delete_product(self, product_id: UUID) -> bool:
        return self.repository.delete(product_id)

    def search_products(self, query: str, skip: int = 0, limit: int = 100) -> List[ProductResponse]:
        products = self.repository.search(query, skip, limit)
        return [ProductResponse.model_validate(prod) for prod in products]
