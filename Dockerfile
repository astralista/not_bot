FROM python:3.9-slim

WORKDIR /app

# Копируем только requirements.txt сначала для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY . .

# Создаем том для данных
VOLUME /app/data

CMD ["python", "bot.py"]