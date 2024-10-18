#!/bin/sh

if [ "$APP_COMMAND" = "celery" ]; then
  celery -A superpool.api.celery worker --loglevel=info
else
  gunicorn --chdir /app/superpool/api --workers 3 --bind :8080 config.wsgi:application
fi
