from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.models.base import Base, UUID


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    nom = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    code = Column(String(20), unique=True, nullable=False)

    # Métadonnées
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    produits = relationship("Product", back_populates="categorie", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(nom='{self.nom}', code='{self.code}')>"
