# Dockerfile
#
# Created: 2024-06-12
FROM python:3.11-slim as builder

ENV POETRY_VERSION=1.8.3
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create $POETRY_VIRTUALENVS_CREATE


# Copy the project files to the container
COPY superpool/api/pyproject.toml superpool/api/poetry.lock /app/

RUN poetry lock --no-update && \
    poetry install --no-root


# Final image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# ENV PYTHONPATH=/app/superpool/api

RUN mkdir /app

WORKDIR /app

# Copy the dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . /app

EXPOSE 8080
EXPOSE 5555

CMD ["gunicorn", "--chdir", "/app/superpool/api", "--workers", "3", "--bind", ":8080", "config.wsgi:application"]
