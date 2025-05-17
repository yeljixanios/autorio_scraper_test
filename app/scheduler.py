# app/scheduler.py
"""Task scheduler for AutoRia scraper."""
import argparse
import asyncio
from datetime import datetime
from typing import Optional

import schedule  

from app.config import config
from app.dumper import dump_database
from app.logger import logger
from app.scraper import AutoRiaScraper
from app.database import init_db

class ScraperScheduler:
    """Scheduler for managing scraping and database dump tasks."""

    def __init__(self):
        """Initialize scheduler with configuration."""
        self.scrape_time = config.SCRAPE_TIME
        self.dump_time = config.DUMP_TIME

    async def _scrape_task(self) -> None:
        """Run scraping task."""
        logger.info("Starting scheduled scraping task")
        async with AutoRiaScraper() as scraper:
            await scraper.process_all_pages()

    async def _dump_task(self) -> None:
        """Run database dump task."""
        logger.info("Starting scheduled database dump task")
        try:
            await dump_database()
            logger.info("Database dump completed successfully")
        except Exception as e:
            logger.error(f"Error during database dump: {str(e)}")

    def schedule_jobs(self) -> None:
        """Schedule scraping and dump jobs using schedule library."""
        scrape_hour, scrape_minute = map(int, self.scrape_time.split(":"))
        dump_hour, dump_minute = map(int, self.dump_time.split(":"))

        # schedule.every().day.at("HH:MM") expects time in 24h format
        schedule.every().day.at(f"{scrape_hour:02d}:{scrape_minute:02d}").do(
            lambda: asyncio.create_task(self._scrape_task())
        )
        schedule.every().day.at(f"{dump_hour:02d}:{dump_minute:02d}").do(
            lambda: asyncio.create_task(self._dump_task())
        )

        logger.info(
            f"Scheduler active:\n"
            f"- Next scraping: {self.scrape_time}\n"
            f"- Next dump: {self.dump_time}"
        )

    async def run(self):
        """Run the scheduler loop."""
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

async def test_run() -> None:
    """Run immediate test of scraping and dumping."""
    logger.info("Starting test run")
    async with AutoRiaScraper() as scraper:
        await scraper.process_all_pages()
    await dump_database()
    logger.info("Test run completed")

async def main() -> None:
    """Main entry point for the scheduler."""
    init_db()

    parser = argparse.ArgumentParser(description="AutoRia Scheduler")
    parser.add_argument(
        "--test-now",
        action="store_true",
        help="Run scraping and dump immediately"
    )
    args = parser.parse_args()

    if args.test_now:
        await test_run()
    else:
        scheduler = ScraperScheduler()
        scheduler.schedule_jobs()
        try:
            await scheduler.run()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler shutdown")

if __name__ == "__main__":
    asyncio.run(main())

