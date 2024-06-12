# Dockerfile
#
# Created: 2024-06-12
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY superpool/pyproject.toml superpool/poetry.lock* /app/

RUN pip install --no-cache-dir poetry

RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Production image (no dev dependencies)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /app

WORKDIR /app

# Copy the dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . /app

# Collect static files
RUN python superpool/manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--chdir", "superpool", "--workers", "3", "--bind", ":8000", "superpool.config.wsgi:application"]

