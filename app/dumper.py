# app/dumper.py
import asyncio
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
from typing import Optional, List
from bs4 import BeautifulSoup

from app.config import config
from app.logger import logger

class DatabaseDumper:
    """Handles database dump operations."""

    def __init__(self, max_dumps: int = 7):
        """Initialize dumper with configuration.
        
        Args:
            max_dumps: Maximum number of dump files to keep
        """
        self.dumps_dir = Path("dumps")
        self.max_dumps = max_dumps
        self._ensure_dumps_directory()

    def _ensure_dumps_directory(self) -> None:
        """Ensure dumps directory exists."""
        self.dumps_dir.mkdir(exist_ok=True)

    def _get_dump_path(self) -> Path:
        """Generate dump file path with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return self.dumps_dir / f"dump_{timestamp}.sql"

    def _get_existing_dumps(self) -> List[Path]:
        """Get list of existing dump files sorted by creation time."""
        return sorted(
            self.dumps_dir.glob("dump_*.sql"),
            key=lambda x: x.stat().st_mtime
        )

    def _cleanup_old_dumps(self) -> None:
        """Remove old dump files keeping only the most recent ones."""
        existing_dumps = self._get_existing_dumps()
        
        if len(existing_dumps) > self.max_dumps:
            dumps_to_remove = existing_dumps[:-self.max_dumps]
            for dump_file in dumps_to_remove:
                try:
                    dump_file.unlink()
                    logger.info(f"Removed old dump: {dump_file}")
                except Exception as e:
                    logger.error(f"Error removing old dump {dump_file}: {str(e)}")

    async def _check_pg_dump_available(self) -> bool:
        """Check if pg_dump is available in the system."""
        try:
            await asyncio.create_subprocess_exec(
                "pg_dump",
                "--version",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False

    async def create_dump(self) -> Optional[Path]:
        """Create database dump asynchronously.
        
        Returns:
            Path to the created dump file or None if dump failed
        """
        if not await self._check_pg_dump_available():
            logger.error("pg_dump not found in system PATH")
            return None

        dump_path = self._get_dump_path()
        logger.info(f"Creating database dump: {dump_path}")

        try:
            process = await asyncio.create_subprocess_exec(
                "pg_dump",
                config.DATABASE_URL,
                "-f", str(dump_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else "Unknown error"
                logger.error(f"Database dump failed: {error_msg}")
                if dump_path.exists():
                    dump_path.unlink()
                return None

            logger.info(f"Database dump completed successfully: {dump_path}")
            self._cleanup_old_dumps()
            return dump_path

        except Exception as e:
            logger.error(f"Error during database dump: {str(e)}")
            if dump_path.exists():
                dump_path.unlink()
            return None

    async def compress_dump(self, dump_path: Path) -> Optional[Path]:
        """Compress dump file using gzip.
        
        Args:
            dump_path: Path to the dump file
            
        Returns:
            Path to the compressed file or None if compression failed
        """
        if not dump_path.exists():
            logger.error(f"Dump file not found: {dump_path}")
            return None

        compressed_path = dump_path.with_suffix('.sql.gz')
        logger.info(f"Compressing dump file: {compressed_path}")

        try:
            process = await asyncio.create_subprocess_exec(
                "gzip",
                "-9",
                str(dump_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else "Unknown error"
                logger.error(f"Dump compression failed: {error_msg}")
                return None

            logger.info(f"Dump compressed successfully: {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"Error compressing dump: {str(e)}")
            return None

    async def get_soup(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object from URL with retries."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use context manager.")

        for attempt in range(retries):
            try:
                async with self.semaphore:
                    async with self.session.get(url) as response:
                        logger.info(f"Requesting {url} - Status: {response.status}")
                        if response.status == 200:
                            html = await response.text()
                            return BeautifulSoup(html, "lxml")
                        elif response.status == 404:
                            logger.warning(f"Page not found: {url}")
                            return None
                        else:
                            logger.error(f"Error {response.status} for {url}")
            except Exception as e:
                logger.error(f"Error getting soup: {str(e)}")
                return None

async def dump_database() -> Optional[Path]:
    """Create and compress database dump.
    
    Returns:
        Path to the compressed dump file or None if operation failed
    """
    dumper = DatabaseDumper()
    dump_path = await dumper.create_dump()
    
    if dump_path:
        return await dumper.compress_dump(dump_path)
    
    return None

cookies = {
    "_504c2": "http://10.42.13.153:3000",
    "advanced_search_test": "42",
    "extendedSearch": "1",
    "gdpr": "[]",
    "informerIndex": "1",
    "ipp": "20",
    "PHPSESSID": "e8EfD4WS7YtYccuu11gOvrNbc2HWkEZd",
    "promolink2": "2",
    "showNewFeatures": "7",
    "showNewNextAdvertisement": "-10",
    "test_new_features": "114",
    "ui": "c0ae13b14440e49d"
}
