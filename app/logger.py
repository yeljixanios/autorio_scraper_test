"""Logging configuration for the application."""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        if not log_file:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"{name}_{current_time}.log"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

# Create default logger
logger = setup_logger(
    name="autoria_scraper",
    log_file="logs/scraper.log",
    level=logging.INFO
)

def get_logger(name: str) -> logging.Logger:
    """Get logger instance by name."""
    return logging.getLogger(name)

logger = logging.getLogger("autoria_scraper")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

