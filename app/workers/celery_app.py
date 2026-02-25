from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery = Celery("empireo", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-tokens-daily": {
            "task": "cleanup_expired_tokens",
            "schedule": crontab(hour=3, minute=0),  # 3 AM UTC daily
        },
        "process-pending-transcriptions-hourly": {
            "task": "transcribe_call_batch",
            "schedule": crontab(minute=0),  # Every hour at :00
        },
        "compute-daily-employee-metrics": {
            "task": "compute_all_employee_metrics",
            "schedule": crontab(hour=6, minute=0),  # 6 AM UTC daily
        },
        "process-file-ingestion-queue-hourly": {
            "task": "process_file_ingestion_batch",
            "schedule": crontab(minute=0),  # Every hour at :00
        },
        "detect-stuck-cases-daily": {
            "task": "detect_stuck_cases",
            "schedule": crontab(hour=7, minute=30),  # 7:30 AM UTC daily (1 PM IST)
        },
    },
)
celery.autodiscover_tasks(["app.workers"])
