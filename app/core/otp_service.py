"""OTP service using Supabase Auth's phone/email OTP.

Supabase handles OTP generation, delivery (SMS/email), and verification.
We call their REST API, then issue our own JWT upon successful verification.
"""

import httpx

from app.config import settings


def _supabase_headers() -> dict:
    return {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }


def _auth_url(path: str) -> str:
    return f"{settings.SUPABASE_URL}/auth/v1{path}"


async def send_phone_otp(phone: str) -> dict:
    """Send OTP to a phone number via Supabase Auth.

    Phone must be in E.164 format (e.g. +918129130745).
    Requires a phone provider (Twilio/Vonage/MessageBird) configured
    in Supabase Dashboard → Authentication → Providers → Phone.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _auth_url("/otp"),
            headers=_supabase_headers(),
            json={"phone": phone},
        )
    data = resp.json() if resp.status_code != 204 else {}
    if resp.status_code in (200, 204):
        return {"ok": True, "message": "OTP sent to phone"}
    return {"ok": False, "error": data.get("msg") or data.get("error_description") or str(data)}


async def send_email_otp(email: str) -> dict:
    """Send OTP to an email address via Supabase Auth.

    Uses Supabase's built-in email provider (no extra config needed).
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _auth_url("/otp"),
            headers=_supabase_headers(),
            json={"email": email},
        )
    data = resp.json() if resp.status_code != 204 else {}
    if resp.status_code in (200, 204):
        return {"ok": True, "message": "OTP sent to email"}
    return {"ok": False, "error": data.get("msg") or data.get("error_description") or str(data)}


async def verify_phone_otp(phone: str, otp_code: str) -> dict:
    """Verify a phone OTP via Supabase Auth.

    Returns the Supabase user data on success, or error on failure.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _auth_url("/verify"),
            headers=_supabase_headers(),
            json={"phone": phone, "token": otp_code, "type": "sms"},
        )
    if resp.status_code == 200:
        return {"ok": True, "supabase_user": resp.json()}
    data = resp.json() if resp.content else {}
    return {"ok": False, "error": data.get("msg") or data.get("error_description") or "Invalid OTP"}


async def verify_email_otp(email: str, otp_code: str) -> dict:
    """Verify an email OTP via Supabase Auth.

    Returns the Supabase user data on success, or error on failure.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _auth_url("/verify"),
            headers=_supabase_headers(),
            json={"email": email, "token": otp_code, "type": "email"},
        )
    if resp.status_code == 200:
        return {"ok": True, "supabase_user": resp.json()}
    data = resp.json() if resp.content else {}
    return {"ok": False, "error": data.get("msg") or data.get("error_description") or "Invalid OTP"}
