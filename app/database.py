# app/database.py
from contextlib import contextmanager
from typing import Generator, Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config import config
from app.models import Base

def create_database_engine() -> Engine:
    """Create database engine with proper configuration."""
    return create_engine(
        config.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
        echo=False  # Set to True for SQL query logging
    )

engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

@contextmanager
def get_db_session() -> Generator[Session, Any, None]:
    """Context manager for database sessions.
    
    Usage:
        with get_db_session() as session:
            session.query(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db() -> None:
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    """Drop all tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)

class DatabaseManager:
    """Database operations manager."""

    @staticmethod
    def add_car(session: Session, car_data: dict) -> None:
        """Add a new car to the database if it doesn't exist."""
        from app.models import Car
        
        # Check if car already exists
        existing_car = session.query(Car).filter(Car.url == car_data['url']).first()
        if not existing_car:
            car = Car(**car_data)
            session.add(car)
            session.commit()

    @staticmethod
    def get_car_by_url(session: Session, url: str) -> Any:
        """Get car by URL."""
        from app.models import Car
        return session.query(Car).filter(Car.url == url).first()

    @staticmethod
    def get_all_cars(session: Session) -> list:
        """Get all cars from database."""
        from app.models import Car
        return session.query(Car).all()

    @staticmethod
    def delete_car(session: Session, url: str) -> None:
        """Delete car by URL."""
        from app.models import Car
        session.query(Car).filter(Car.url == url).delete()
        session.commit()
