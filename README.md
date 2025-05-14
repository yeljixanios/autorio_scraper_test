# AutoRia Scraper

Асинхронний скрапер для збору оголошень про б/у авто з [AutoRia](https://auto.ria.com) із автоматичним збереженням у PostgreSQL та щоденним дампом БД. Підтримує запуск у Docker.

---

## 🔧 Можливості

- ⚡ Асинхронний скрапінг (`aiohttp`, `asyncio`)
- 🔁 Відсутність дублів (унікальність по URL)
- 💾 Щоденний дамп БД у папку `dumps/`
- ⚙️ Налаштування через `.env`
- 📝 Логування
- 🐳 Docker / Docker Compose підтримка

---

## 📁 Структура проєкту

```
autoria_scraper/
├── app/                        # Основний код застосунку
│   ├── scraper.py              # Логіка скрапінгу AutoRia
│   ├── models.py               # SQLAlchemy-моделі
│   ├── scheduler.py            # Планувальник задач
│   ├── config.py               # Завантаження конфігів з .env
│   ├── logger.py               # Логування
│   └── ...                     # Інші модулі (dumper, db, utils тощо)
├── dumps/                      # Автоматичні дампи БД
├── logs/                       # Логи роботи
├── requirements.txt            # Залежності
├── README.md                   # Цей файл
├── .env                        # Налаштування середовища
├── docker-compose.yml          # Docker Compose конфіг
└── Dockerfile                  # Docker-образ
```

---

## ⚙️ Налаштування

Створіть файл `.env` у корені проєкту зі змінними:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/autoria
START_URL=https://auto.ria.com/uk/car/used/
SCRAPE_TIME=12:00
DUMP_TIME=12:05
CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
RETRY_DELAY=5
```

---

## 🚀 Запуск

### 1. Клонування репозиторію

```bash
git clone <repository-url>
cd autoria_scraper
```

### 2. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 3. Створіть `.env`, як описано вище.

### 4. Запуск через Docker

```bash
docker-compose up -d --build
```

Або з попереднім білдом:

```bash
docker-compose build
docker-compose up -d
```

### 5. Локальний запуск без Docker

```bash
python -m app.scheduler
```

### 6. Тестовий запуск без очікування часу

```bash
python -m app.scheduler --test-now
```

---

## 🗃️ Схема БД

| Поле           | Тип      | Опис                        |
|----------------|----------|-----------------------------|
| `url`          | string   | Унікальний URL оголошення   |
| `title`        | string   | Назва авто                  |
| `price_usd`    | integer  | Ціна в доларах              |
| `odometer`     | integer  | Пробіг (км)                 |
| `username`     | string   | Ім’я продавця               |
| `phone_number` | string   | Номер телефону              |
| `image_url`    | string   | Посилання на головне фото  |
| `images_count` | integer  | Кількість фото              |
| `car_number`   | string   | Номер авто                  |
| `car_vin`      | string   | VIN-код                     |
| `datetime_found` | datetime | Дата/час скрапінгу        |

---

## 📦 Дампи БД

Файли дампу зберігаються у каталозі `dumps/` у стиснутому форматі. Назва включає дату створення.

---

