from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base
from app.config import settings

engine = create_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_pre_ping=settings.database.pool_pre_ping
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def reset_database():
    """Drop all tables and recreate them (for development/testing)"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
