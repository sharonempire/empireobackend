"""Email generation and delivery service."""

import logging
from typing import Any

import httpx

from app.config import settings
from app.core.openai_service import chat_completion

logger = logging.getLogger("empireo.email")

# Template system prompts for each email type
_TEMPLATE_PROMPTS: dict[str, str] = {
    "follow_up": (
        "You are an email writer for Empireo, a study abroad consultancy. "
        "Write a professional follow-up email to a prospective student. "
        "Be warm, helpful, and encourage them to take the next step. "
        "Keep the email concise (under 200 words). "
        "Return JSON with keys: subject, body, tone."
    ),
    "docs_request": (
        "You are an email writer for Empireo, a study abroad consultancy. "
        "Write a professional email requesting specific documents from a student "
        "for their application process. Be clear about what is needed and any deadlines. "
        "Keep it under 200 words. "
        "Return JSON with keys: subject, body, tone."
    ),
    "offer_congrats": (
        "You are an email writer for Empireo, a study abroad consultancy. "
        "Write a congratulatory email to a student who has received an offer from a university. "
        "Be enthusiastic but professional. Mention next steps they should take. "
        "Keep it under 200 words. "
        "Return JSON with keys: subject, body, tone."
    ),
    "payment_reminder": (
        "You are an email writer for Empireo, a study abroad consultancy. "
        "Write a polite payment reminder email to a student. Include the payment details "
        "and deadline from the context. Be firm but courteous. "
        "Keep it under 150 words. "
        "Return JSON with keys: subject, body, tone."
    ),
    "welcome": (
        "You are an email writer for Empireo, a study abroad consultancy. "
        "Write a warm welcome email to a new student who has just registered. "
        "Introduce the services Empireo offers and what the student can expect. "
        "Keep it under 200 words. "
        "Return JSON with keys: subject, body, tone."
    ),
}


async def generate_email(template_type: str, context: dict[str, Any]) -> dict[str, str]:
    """Generate an email using an AI template and context variables.

    Args:
        template_type: One of "follow_up", "docs_request", "offer_congrats",
                       "payment_reminder", "welcome".
        context: Dictionary of context variables to include in the email
                 (e.g. student_name, university_name, documents_needed, etc.).

    Returns:
        Dict with keys: subject, body, tone.
    """
    system_prompt = _TEMPLATE_PROMPTS.get(template_type)
    if system_prompt is None:
        raise ValueError(
            f"Unknown template type '{template_type}'. "
            f"Valid types: {', '.join(_TEMPLATE_PROMPTS.keys())}"
        )

    context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
    user_message = f"Context:\n{context_str}\n\nGenerate the email."

    result = await chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.5,
        json_mode=True,
    )

    import json

    parsed = json.loads(result["content"])
    return {
        "subject": parsed.get("subject", ""),
        "body": parsed.get("body", ""),
        "tone": parsed.get("tone", "professional"),
    }


async def send_email(
    to: str,
    subject: str,
    body: str,
    from_name: str = "Empireo",
) -> dict[str, Any]:
    """Send an email via the SendGrid API.

    If SENDGRID_API_KEY is not configured, the send is skipped and logged.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body (HTML supported).
        from_name: Sender display name.

    Returns:
        Dict with status and message_id (or skip reason).
    """
    api_key = settings.SENDGRID_API_KEY
    if not api_key:
        logger.info("Email send skipped (no SENDGRID_API_KEY): to=%s subject=%s", to, subject)
        return {"status": "skipped", "reason": "no API key"}

    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": "noreply@empireo.co", "name": from_name},
        "subject": subject,
        "content": [{"type": "text/html", "value": body}],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        if response.status_code in (200, 202):
            message_id = response.headers.get("X-Message-Id", "")
            logger.info("Email sent to %s (message_id=%s)", to, message_id)
            return {"status": "sent", "message_id": message_id}
        else:
            logger.error(
                "SendGrid error: status=%d body=%s", response.status_code, response.text
            )
            return {"status": "error", "detail": response.text}
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
