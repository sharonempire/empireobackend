from app.workers.celery_app import celery_app


@celery_app.task(name="send_notification")
def send_notification(user_id: str, title: str, message: str):
    print(f"[NOTIFICATION] -> {user_id}: {title}")
    return {"status": "sent"}


@celery_app.task(name="score_lead")
def score_lead(lead_id: str):
    print(f"[AI SCORING] -> Lead {lead_id}")
    return {"status": "scored"}
