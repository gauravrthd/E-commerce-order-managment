
from celery import Celery

from config.settings import settings

celery_app = Celery(
    "ecommerce",
    broker=settings.CELERY_BROKER_URL,
    include=["celery_app.email_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    task_publish_retry=True
)
