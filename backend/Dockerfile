FROM python:3.12

WORKDIR /app

# Устанавливаем зависимости из сгенерированного requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY app/ ./app/

# Загружаем модель spaCy
RUN python -m spacy download en_core_web_lg

# Директория для логов
RUN mkdir -p /app/logs

# Переменные окружения по умолчанию
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=password
ENV SPACY_MODEL=en_core_web_lg
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]