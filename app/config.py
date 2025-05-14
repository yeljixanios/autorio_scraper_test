"""Configuration module for the AutoRia scraper."""
from dataclasses import dataclass
from datetime import datetime
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_time_format(time_str: str) -> bool:
    """Validate if the time string is in HH:MM format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

@dataclass
class Config:
    """Application configuration settings."""
    DATABASE_URL: str
    SCRAPE_TIME: str
    DUMP_TIME: str
    START_URL: str
    CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 30
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 5
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set in environment variables")
        
        if not self.START_URL:
            raise ValueError("START_URL must be set in environment variables")
        
        if not validate_time_format(self.SCRAPE_TIME):
            raise ValueError("SCRAPE_TIME must be in HH:MM format")
        
        if not validate_time_format(self.DUMP_TIME):
            raise ValueError("DUMP_TIME must be in HH:MM format")

# Create configuration instance
config = Config(
    DATABASE_URL=os.getenv("DATABASE_URL", ""),
    SCRAPE_TIME=os.getenv("SCRAPE_TIME", "12:00"),
    DUMP_TIME=os.getenv("DUMP_TIME", "12:05"),
    START_URL=os.getenv("START_URL", ""),
)
