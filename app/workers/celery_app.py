from celery import Celery

from app.config import settings

celery = Celery("empireo", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
celery.autodiscover_tasks(["app.workers"])
