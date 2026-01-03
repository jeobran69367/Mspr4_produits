from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class CategoryBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    code: str = Field(..., min_length=1, max_length=20)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    code: Optional[str] = Field(None, min_length=1, max_length=20)


class CategoryResponse(CategoryBase):
    id: UUID
    date_creation: datetime
    date_modification: datetime

    class Config:
        from_attributes = True
