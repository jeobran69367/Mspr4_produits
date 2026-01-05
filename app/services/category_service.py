from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate


class CategoryService:
    def __init__(self, db: Session):
        self.repository = CategoryRepository(db)

    def get_categories(self, skip: int = 0, limit: int = 100) -> List[CategoryResponse]:
        categories = self.repository.get_all(skip, limit)
        return [CategoryResponse.model_validate(cat) for cat in categories]

    def get_category(self, category_id: UUID) -> Optional[CategoryResponse]:
        category = self.repository.get_by_id(category_id)
        return CategoryResponse.model_validate(category) if category else None

    def create_category(self, category: CategoryCreate) -> CategoryResponse:
        # Check if category with same code exists
        existing = self.repository.get_by_code(category.code)
        if existing:
            raise ValueError(f"Category with code '{category.code}' already exists")

        db_category = self.repository.create(category)
        return CategoryResponse.model_validate(db_category)

    def update_category(self, category_id: UUID, category_update: CategoryUpdate) -> Optional[CategoryResponse]:
        # If code is being updated, check it doesn't conflict
        if category_update.code:
            existing = self.repository.get_by_code(category_update.code)
            if existing and existing.id != category_id:
                raise ValueError(f"Category with code '{category_update.code}' already exists")

        updated_category = self.repository.update(category_id, category_update)
        return CategoryResponse.model_validate(updated_category) if updated_category else None

    def delete_category(self, category_id: UUID) -> bool:
        return self.repository.delete(category_id)
