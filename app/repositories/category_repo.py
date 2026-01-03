from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        return self.db.query(Category).offset(skip).limit(limit).all()

    def get_by_id(self, category_id: UUID) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_by_code(self, code: str) -> Optional[Category]:
        return self.db.query(Category).filter(Category.code == code).first()

    def create(self, category: CategoryCreate) -> Category:
        db_category = Category(**category.model_dump())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def update(self, category_id: UUID, category_update: CategoryUpdate) -> Optional[Category]:
        db_category = self.get_by_id(category_id)
        if db_category:
            update_data = category_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_category, field, value)
            self.db.commit()
            self.db.refresh(db_category)
        return db_category

    def delete(self, category_id: UUID) -> bool:
        db_category = self.get_by_id(category_id)
        if db_category:
            self.db.delete(db_category)
            self.db.commit()
            return True
        return False
