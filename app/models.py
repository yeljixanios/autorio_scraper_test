# app/models.py
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

Base = declarative_base()

class Car(Base):
    """Model representing a car listing from AutoRia."""
    
    __tablename__ = 'cars'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    price_usd = Column(Integer)
    odometer = Column(Integer)
    username = Column(String)
    phone_number = Column(BigInteger)
    image_url = Column(String)
    images_count = Column(Integer)
    car_number = Column(String)
    car_vin = Column(String)
    datetime_found = Column(DateTime, default=datetime.utcnow, nullable=False)

    @validates('url')
    def validate_url(self, key: str, url: str) -> str:
        """Validate URL format."""
        if not url.startswith('http'):
            raise ValueError("URL must start with http/https")
        return url

    @validates('price_usd', 'odometer', 'images_count')
    def validate_positive_numbers(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate that numeric values are positive."""
        if value is not None and value < 0:
            raise ValueError(f"{key} must be a positive number")
        return value

    @validates('phone_number')
    def validate_phone(self, key: str, number: Optional[str]) -> Optional[int]:
        """Convert phone number string to integer.
        
        Example: '+380501234567' -> 380501234567
        """
        if not number:
            return None
            
        # Remove any non-digit characters
        digits = ''.join(filter(str.isdigit, str(number)))
        if not digits:
            return None
            
        try:
            return int(digits)
        except ValueError:
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'price_usd': self.price_usd,
            'odometer': self.odometer,
            'username': self.username,
            'phone_number': self.phone_number,
            'image_url': self.image_url,
            'images_count': self.images_count,
            'car_number': self.car_number,
            'car_vin': self.car_vin,
            'datetime_found': self.datetime_found.isoformat() if self.datetime_found else None
        }

    def __repr__(self) -> str:
        """String representation of the Car model."""
        return f"<Car(id={self.id}, title='{self.title}', price_usd={self.price_usd})>"

@event.listens_for(Car, 'before_insert')
def normalize_data(mapper: Any, connection: Any, target: Car) -> None:
    """Normalize data before inserting into database."""
    # Convert empty strings to None
    for column in mapper.columns:
        if getattr(target, column.key) == "":
            setattr(target, column.key, None)
    
    # Normalize phone number
    if target.phone_number and isinstance(target.phone_number, str):
        target.phone_number = int(target.phone_number.replace(' ', '').replace('-', ''))
