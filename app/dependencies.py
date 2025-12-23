from sqlalchemy.orm import Session
from app.database import get_db


def get_database() -> Session:
    """
    Dependency to get database session
    """
    return get_db()
