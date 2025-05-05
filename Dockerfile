FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем директорию для данных, если её нет
RUN mkdir -p /app/data

CMD ["python", "main.py"]
