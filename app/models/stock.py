import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import UUID, Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Relation avec produit
    produit_id = Column(UUID(), ForeignKey("products.id"), nullable=False, unique=True)
    produit = relationship("Product", back_populates="stock")

    # Quantités
    quantite_disponible = Column(Integer, nullable=False, default=0)
    quantite_reservee = Column(Integer, default=0)
    quantite_minimum = Column(Integer, default=10)  # Seuil d'alerte
    quantite_maximum = Column(Integer, default=1000)  # Capacité stockage

    # Alertes
    alerte_stock_bas = Column(Boolean, default=False)

    # Métadonnées
    date_derniere_entree = Column(DateTime)
    date_derniere_sortie = Column(DateTime)
    date_modification = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Stock(produit_id='{self.produit_id}', disponible={self.quantite_disponible})>"
