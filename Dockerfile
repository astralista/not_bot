FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Инициализация БД при сборке
RUN python init_db.py

CMD ["python", "bot.py"]