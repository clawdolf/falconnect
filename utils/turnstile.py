"""Cloudflare Turnstile verification for public lead endpoints.

Verifies a client-supplied Turnstile token against Cloudflare's siteverify
API. If TURNSTILE_SECRET is unset, verification is skipped and the caller
is allowed through — this lets the backend deploy before the frontend has
the sitekey wired up. Rate limiting + the honeypot field are the second
line of defence so skipping Turnstile does not leave the endpoint naked.

Fails open on Cloudflare 5xx (siteverify unreachable) so we do not lose
legitimate leads during a Cloudflare outage.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger("falconconnect.turnstile")

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: Optional[str], client_ip: Optional[str] = None) -> bool:
    """Return True if the Turnstile token is valid, False otherwise.

    Returns True (pass-through) when TURNSTILE_SECRET is unset, so the
    system can be deployed incrementally. Returns True on siteverify 5xx
    (fail-open for Cloudflare outages).
    """
    settings = get_settings()
    secret = settings.turnstile_secret

    if not secret:
        # Not configured — rely on honeypot + rate limit.
        return True

    if not token:
        logger.warning("Turnstile: missing token on authenticated request")
        return False

    data = {"secret": secret, "response": token}
    if client_ip:
        data["remoteip"] = client_ip

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(SITEVERIFY_URL, data=data)
        if resp.status_code >= 500:
            logger.warning(
                "Turnstile siteverify 5xx (%s) — failing open to avoid lead loss",
                resp.status_code,
            )
            return True
        payload = resp.json()
        if payload.get("success"):
            return True
        logger.info(
            "Turnstile rejected token: codes=%s ip=%s",
            payload.get("error-codes"),
            client_ip,
        )
        return False
    except httpx.RequestError as exc:
        logger.warning("Turnstile network error (%s) — failing open", exc)
        return True
