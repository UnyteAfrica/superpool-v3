import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("superpool",
    broker=os.getenv("CELERY_BROKER_URL", default="redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", default="redis://redis:6379/0"),
)

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()