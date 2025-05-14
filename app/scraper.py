import asyncio
import re
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.config import config
from app.database import get_db_session, DatabaseManager
from app.logger import logger
from app.models import Car


class AutoRiaScraper:
    def __init__(self):
        self.start_url = config.START_URL
        self.headers = {"User-Agent": config.USER_AGENT}
        self.timeout = ClientTimeout(total=30)
        self.session: Optional[aiohttp.ClientSession] = None
        self.db_manager = DatabaseManager()
        self.semaphore = asyncio.Semaphore(config.CONCURRENT_REQUESTS)
        self.driver = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_soup(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object from URL with retries."""
        for attempt in range(retries):
            try:
                async with self.semaphore:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            return BeautifulSoup(html, "lxml")
                        logger.warning(f"Unexpected status {response.status} on {url}")
            except Exception as e:
                logger.error(f"Exception: {e}")
                await asyncio.sleep(config.RETRY_DELAY * (attempt + 1))
        return None

    def extract_car_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract car URLs from the soup object."""
        car_links = []
        selectors = [
            "a.m-link-ticket",
            "a.address",
            "div.ticket-title a",
            "div.head-ticket a",
            "div.content-bar a[href*='auto_']"
        ]
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                car_url = link.get("href")
                if car_url and "auto_" in car_url:
                    car_links.append(car_url)
        return list(set(car_links))

    def normalize_odometer(self, text: str) -> int:
        if not text:
            return 0
        
        original_text = text
        
        # Handle thousand abbreviations
        match_thousand = re.search(r"(\d+)\s*тис", original_text)
        if match_thousand:
            return int(match_thousand.group(1)) * 1000
        
        # Remove non-digit characters
        text = text.replace("\xa0", " ").replace("км", "").replace(",", "").strip()
        
        # Extract digits
        digits = re.findall(r"\d+", text)
        if digits:
            value = int("".join(digits))
            # Sanity check - most cars have less than 1 million km
            if value > 1000000:
                logger.warning(f"Unreasonable odometer value: {value}, capping at 999999")
                return 999999
            return value
        
        return 0

    def start_driver(self):
        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            # Add these options to help with stability
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            try:
                self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                logger.error(f"Failed to start Chrome driver: {e}")
                # Fallback to not using Selenium for phone numbers
                self.driver = None

    def stop_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_phone_number_selenium(self, url: str) -> str:
        if not self.driver:
            self.start_driver()
            if not self.driver:  # Если драйвер все равно не запустился
                return ""
        
        try:
            self.driver.get(url)

            try:

                show_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.phone_show_link"))
                )
                show_btn.click()
                

                phone_el = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "span.phone.bold"))
                )
                
                # Получаем текст телефона
                phone = phone_el.text.strip()
                logger.info(f"Found phone number: {phone}")
                
                # Normalize number (keep only digits, add 380 if needed)
                digits = ''.join(filter(str.isdigit, phone))
                if digits.startswith("380"):
                    return digits
                elif digits.startswith("0") and len(digits) == 10:
                    return "38" + digits
                elif digits.startswith("8") and len(digits) == 11:
                    return "3" + digits
                elif digits.startswith("9") and len(digits) == 9:
                    return "380" + digits
                return digits
            except Exception as e:
                logger.warning(f"Could not get phone number via Selenium: {e}")
                

                try:
                    phone_elements = self.driver.find_elements(By.CSS_SELECTOR, "span.phone.bold")
                    if phone_elements:
                        phone = phone_elements[0].text.strip()
                        if phone and not "xxx" in phone: 
                            logger.info(f"Found phone directly: {phone}")
                            digits = ''.join(filter(str.isdigit, phone))
                            return digits
                except Exception as inner_e:
                    logger.warning(f"Failed to find phone directly: {inner_e}")
                
                return ""
        except Exception as e:
            logger.error(f"Selenium error: {e}")
            # Close and restart driver on error
            self.stop_driver()
            return ""

    async def get_phone_number_selenium_async(self, url: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_phone_number_selenium, url)

    def get_phone_number(self, url: str, cookies: dict) -> str:
        return self.get_phone_number_selenium(url)

    async def parse_car_page(self, soup: BeautifulSoup, url: str, cookies: dict) -> dict:
        try:
            # Title + year
            title_el = soup.select_one("h1.head")
            title = title_el.text.strip() if title_el else ""
            if not title:
                logger.warning(f"No title found for {url}")
                return None
            
            # Ціна
            price_el = soup.select_one(".price_value strong")
            price_usd = int(re.sub(r"[^\d]", "", price_el.text)) if price_el else 0

            # Пробіг
            odometer = 0
            for label in soup.find_all("span", class_="label"):
                if "Пробіг від продавця" in label.get_text():
                    argument = label.find_next_sibling("span", class_="argument")
                    if argument:
                        odometer = self.normalize_odometer(argument.get_text())
                    break

            # Ім'я продавця
            username_el = soup.select_one(".seller_info_name")
            username = username_el.text.strip() if username_el else ""

            # Фото
            images = soup.select("div.photo-620x465 img")
            image_url = images[0]["src"] if images else ""
            images_count = len(images)

            # Держномер (тільки номер)
            car_number = ""
            car_number_el = soup.find("span", class_="state-num")
            if car_number_el:
                try:
                    match = re.search(r"[A-ZА-ЯІЇЄ]{2}\s?\d{4}\s?[A-ZА-ЯІЇЄ]{2}", car_number_el.text)
                    car_number = match.group(0) if match else car_number_el.text.strip()
                except (AttributeError, TypeError):
                    # Handle case when car_number_el.text is None or not a string
                    pass

            # VIN
            car_vin = ""
            vin_el = soup.find(string=re.compile("VIN", re.I))
            if vin_el:
                # Шукаємо 17-значний VIN у сусідньому елементі
                parent = vin_el.parent
                vin_match = re.search(r"[A-HJ-NPR-Z0-9]{17}", parent.get_text())
                if vin_match:
                    car_vin = vin_match.group(0)

            # Телефон
            phone_number = self.get_phone_number(url, cookies)

            return {
                "url": url,
                "title": title,
                "price_usd": price_usd,
                "odometer": odometer,
                "username": username or "",  # Ensure not None
                "phone_number": phone_number or "",  # Ensure not None
                "image_url": image_url or "",  # Ensure not None
                "images_count": images_count,
                "car_number": car_number or "",  # Ensure not None
                "car_vin": car_vin or "",  # Ensure not None
                "datetime_found": datetime.utcnow(),
            }
        except Exception as e:
            logger.error(f"Failed to parse {url}: {e}")
            return None

    async def process_car_urls(self, urls: List[str], session: Session, cookies: dict) -> int:
        async def get_and_parse(url):
            try:
                soup = await self.get_soup(url)
                if soup:
                    return await self.parse_car_page(soup, url, cookies)
                return None
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                return None
            
        tasks = [get_and_parse(url) for url in urls]
        car_data_list = await asyncio.gather(*tasks, return_exceptions=False)
        
        saved = 0
        for car in car_data_list:
            if car is None:
                continue
            try:
                self.db_manager.add_car(session, car)
                saved += 1
                logger.info(f"Saved: {car['title']}")
            except Exception as e:
                logger.error(f"DB error: {e}")
                # Try to rollback if possible
                try:
                    session.rollback()
                except:
                    pass
        return saved

    async def process_all_pages(self):
        """Main method to run the scraper."""
        logger.info("Starting AutoRia scraper...")
        total_cars_saved = 0

        page_number = 1
        while True:
            url = f"{self.start_url}?page={page_number}"
            logger.info(f"Processing page {page_number}: {url}")

            soup = await self.get_soup(url)
            if not soup:
                logger.error(f"Failed to get soup for page {page_number}")
                break

            car_urls = self.extract_car_urls(soup)
            if not car_urls:
                logger.info("No more pages to process")
                break

            with get_db_session() as session:
                cookies = {}  # Implement cookies handling
                saved = await self.process_car_urls(car_urls, session, cookies)
                total_cars_saved += saved

            page_number += 1

        logger.info(f"Scraping completed. Total cars saved: {total_cars_saved}")
        return total_cars_saved


async def main():
    async with AutoRiaScraper() as scraper:
        await scraper.process_all_pages()


if __name__ == "__main__":
    asyncio.run(main())
