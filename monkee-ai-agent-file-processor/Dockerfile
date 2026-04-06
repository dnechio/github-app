FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry==1.8.0 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only=main --no-interaction --no-ansi

COPY . .

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "-c", "4"]
