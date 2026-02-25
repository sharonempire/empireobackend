"""Firebase Cloud Messaging (FCM) push notification service.

Mirrors the Supabase Edge Function `Notification` (v18) which sends FCM
pushes via the Google Auth HTTP v1 API.

Requires GOOGLE_SERVICE_ACCOUNT_JSON env var (path to service account JSON)
or GOOGLE_SERVICE_ACCOUNT_KEY (inline JSON string).
"""

import json
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("empireo.fcm")

# Google OAuth2 token cache
_cached_token: str | None = None
_token_expiry: float = 0


def _get_google_access_token() -> str:
    """Get a Google OAuth2 access token for FCM using service account credentials.

    Uses the JWT-based approach matching the Edge Function's google-auth-library usage.
    """
    global _cached_token, _token_expiry

    if _cached_token and time.time() < _token_expiry - 60:
        return _cached_token

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        sa_key = settings.GOOGLE_SERVICE_ACCOUNT_KEY
        if not sa_key:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_KEY not configured")

        if sa_key.startswith("{"):
            info = json.loads(sa_key)
        else:
            with open(sa_key) as f:
                info = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        credentials.refresh(Request())
        _cached_token = credentials.token
        _token_expiry = time.time() + 3500  # Tokens valid ~3600s
        return _cached_token

    except ImportError:
        logger.warning("google-auth not installed, using JWT fallback")
        return _get_token_jwt_fallback()


def _get_token_jwt_fallback() -> str:
    """Fallback: manually construct JWT and exchange for access token."""
    global _cached_token, _token_expiry

    import base64
    import hashlib
    import hmac

    from jose import jwt as jose_jwt

    sa_key = settings.GOOGLE_SERVICE_ACCOUNT_KEY
    if not sa_key:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_KEY not configured")

    info = json.loads(sa_key) if sa_key.startswith("{") else json.load(open(sa_key))

    now = int(time.time())
    payload = {
        "iss": info["client_email"],
        "scope": "https://www.googleapis.com/auth/firebase.messaging",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }

    from cryptography.hazmat.primitives import serialization

    private_key = serialization.load_pem_private_key(
        info["private_key"].encode(), password=None
    )

    from jose import jwt as jose_jwt

    assertion = jose_jwt.encode(payload, info["private_key"], algorithm="RS256")

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    _cached_token = data["access_token"]
    _token_expiry = time.time() + data.get("expires_in", 3500)
    return _cached_token


def _get_project_id() -> str:
    """Extract Firebase project ID from service account credentials."""
    sa_key = settings.GOOGLE_SERVICE_ACCOUNT_KEY
    if not sa_key:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_KEY not configured")
    info = json.loads(sa_key) if sa_key.startswith("{") else json.load(open(sa_key))
    return info["project_id"]


async def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    image: str | None = None,
) -> dict[str, Any]:
    """Send a single FCM push notification via the HTTP v1 API.

    This mirrors the Supabase Edge Function `Notification` which:
    1. Gets a Google OAuth2 access token
    2. POSTs to FCM HTTP v1 endpoint
    3. Handles token and message errors

    Args:
        fcm_token: Device FCM registration token
        title: Notification title
        body: Notification body text
        data: Optional key-value data payload
        image: Optional image URL for rich notifications

    Returns:
        dict with status and FCM message name/error
    """
    try:
        access_token = _get_google_access_token()
        project_id = _get_project_id()
    except Exception as e:
        logger.error("FCM auth failed: %s", e)
        return {"status": "error", "error": f"auth_failed: {e}"}

    message: dict[str, Any] = {
        "token": fcm_token,
        "notification": {"title": title, "body": body},
    }

    if image:
        message["notification"]["image"] = image

    if data:
        message["data"] = {k: str(v) for k, v in data.items()}

    # Android-specific config for high priority
    message["android"] = {
        "priority": "high",
        "notification": {"sound": "default", "click_action": "FLUTTER_NOTIFICATION_CLICK"},
    }

    # APNs config for iOS
    message["apns"] = {
        "payload": {"aps": {"sound": "default", "badge": 1}},
    }

    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json={"message": message},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )

    if resp.status_code == 200:
        result = resp.json()
        logger.info("FCM push sent: %s", result.get("name"))
        return {"status": "sent", "message_name": result.get("name")}
    else:
        error_body = resp.text
        logger.error("FCM push failed (%d): %s", resp.status_code, error_body[:500])
        return {"status": "error", "http_status": resp.status_code, "error": error_body[:500]}


async def send_push_to_user(
    db,
    user_id: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> list[dict]:
    """Send push notification to all registered devices of a user.

    Looks up FCM tokens from both user_push_tokens and user_fcm_tokens tables.
    """
    from sqlalchemy import select, or_

    from app.modules.push_tokens.models import UserFCMToken, UserPushToken

    # Gather all tokens for this user
    tokens = set()

    push_result = await db.execute(
        select(UserPushToken.fcm_token).where(UserPushToken.user_id == user_id)
    )
    for row in push_result.all():
        if row[0]:
            tokens.add(row[0])

    fcm_result = await db.execute(
        select(UserFCMToken.fcm_token).where(UserFCMToken.user_id == user_id)
    )
    for row in fcm_result.all():
        if row[0]:
            tokens.add(row[0])

    if not tokens:
        return [{"status": "no_tokens", "user_id": user_id}]

    results = []
    for token in tokens:
        result = await send_push_notification(token, title, body, data)
        result["fcm_token"] = token[:20] + "..."
        results.append(result)

    return results
