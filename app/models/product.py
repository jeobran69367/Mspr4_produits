from sqlalchemy import Column, String, Numeric, Text, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from app.models.base import Base


class ProductStatus(str, PyEnum):
    ACTIF = "actif"
    RUPTURE = "rupture"
    ARCHIVE = "archive"
    EN_ATTENTE = "en_attente"


class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    nom = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Relations
    categorie_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    categorie = relationship("Category", back_populates="produits")
    
    # Prix
    prix_ht = Column(Numeric(10, 2), nullable=False)
    taux_tva = Column(Numeric(4, 2), default=20.0)  # 20% par défaut
    prix_ttc = Column(Numeric(10, 2), nullable=False)  # Calculé
    
    # Caractéristiques
    unite_mesure = Column(String(20), default="g")  # g, kg, L, pièce
    poids_unitaire = Column(Numeric(8, 3))  # en grammes
    fournisseur = Column(String(100))
    origine = Column(String(100))  # Pays d'origine
    notes_qualite = Column(Text)  # "Arabica 100%", "Bio", etc.
    
    # Métadonnées
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    statut = Column(Enum(ProductStatus), default=ProductStatus.ACTIF)
    
    # Relations
    stock = relationship("Stock", uselist=False, back_populates="produit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(sku='{self.sku}', nom='{self.nom}', statut='{self.statut}')>"
