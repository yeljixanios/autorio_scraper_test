# AutoRia Scraper

Асинхронний скрапер для збору оголошень про б/у авто з AutoRia з автоматичним збереженням у PostgreSQL та щоденним дампом БД.

## Можливості

- Асинхронний скрапінг (`aiohttp`, `asyncio`)
- Відсутність дублів (унікальність по url)
- Щоденний дамп БД у папку `dumps/`
- Налаштування через `.env`
- Логування
- Docker/Docker Compose підтримка

## Структура проєкту

```
## Структура проєкту

```
autoria_scraper/
├── app/                        # Основний код застосунку
│   ├── scraper.py              # Логіка асинхронного скрапінгу AutoRia
│   ├── models.py               # SQLAlchemy моделі (схема БД)
│   ├── scheduler.py            # Планувальник задач (scraping, дамп)
│   ├── config.py               # Завантаження та валідація налаштувань з .env
│   ├── logger.py               # Налаштування логування
│   └── ...                     # Інші допоміжні модулі (dumper, database тощо)
├── dumps/     
├── logs/                  
├── requirements.txt            
├── README.md                   # Цей файл з інструкціями
├── .env                        
└── docker-compose.yml    
└── Dockerfile      
```

## Налаштування

За відсутності, створіть файл `.env` у корені проєкту зі змінними:

```
DATABASE_URL=postgresql://user:password@localhost:5432/autoria
START_URL=https://auto.ria.com/uk/car/used/
SCRAPE_TIME=12:00
DUMP_TIME=12:05
CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=5
```

## Кроки запуску

1. Клонувати репозиторій:
    ```bash
    git clone <repository-url>
    cd autoria_scraper
    ```

2. Встановити залежності:
    ```bash
    pip install -r requirements.txt
    ```

3. Створити файл `.env` (див. вище).

4. Зібрати Docker-образи і Запустити через Docker:
    ```bash
    docker-compose build

    docker-compose up -d
    ```
    або 
 
    Запустити через Docker (з автоматичним білдом, якщо потрібно):
    ```bash
    docker-compose up -d --build
    ```
   або локально:
    ```bash
    python -m app.scheduler
    ```

5. Для разового тестового запуску (без очікування часу):
    ```bash
    python -m app.scheduler --test-now
    ```

## Схема БД

- url (string, унікальний)
- title (string)
- price_usd (integer)
- odometer (integer, наприклад 95000)
- username (string)
- phone_number (string)
- image_url (string)
- images_count (integer)
- car_number (string)
- car_vin (string)
- datetime_found (datetime)

## Дамп БД

Файли дампу зберігаються у папці `dumps/` у стиснутому вигляді.
