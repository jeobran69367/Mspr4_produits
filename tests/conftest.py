import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.base import Base
from app.database import get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_category():
    """Sample category data"""
    return {
        "nom": "Arabica",
        "description": "Café Arabica de qualité supérieure",
        "code": "ARAB"
    }


@pytest.fixture
def sample_product(sample_category_id):
    """Sample product data"""
    return {
        "sku": "CAFE-001",
        "nom": "Café Arabica Premium",
        "description": "Café Arabica d'exception",
        "categorie_id": str(sample_category_id),
        "prix_ht": "15.99",
        "taux_tva": "20.0",
        "unite_mesure": "g",
        "poids_unitaire": "250",
        "fournisseur": "Fournisseur Test",
        "origine": "Colombie"
    }
