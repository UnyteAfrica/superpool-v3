from celery import Celery

app = Celery(
    "superpool", broker=env("CELERY_BROKER_URL", default="redis://redis:6379/0")
)
