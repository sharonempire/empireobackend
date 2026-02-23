from app.workers.celery_app import celery


@celery.task(name="send_notification")
def send_notification(user_id: str, title: str, message: str, notification_type: str = "general"):
    """Placeholder task for sending notifications asynchronously."""
    return {"user_id": user_id, "title": title, "status": "sent"}


@celery.task(name="process_document")
def process_document(document_id: str):
    """Placeholder task for document post-processing."""
    return {"document_id": document_id, "status": "processed"}
