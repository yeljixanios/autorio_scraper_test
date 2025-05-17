FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 scraper
RUN mkdir -p /app/dumps /app/logs && chown -R scraper:scraper /app

USER scraper

ENV PYTHONPATH="/app:$PYTHONPATH"

CMD ["python", "-m", "app.scheduler"]