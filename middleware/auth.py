"""Clerk authentication middleware for FastAPI.

Verifies Clerk session JWTs using the Clerk Backend API.
Falls through gracefully if CLERK_SECRET_KEY is not configured (returns a
placeholder user so the app still runs during development before Clerk keys
are provided).

Usage:
    from middleware.auth import require_auth
    @router.get("/protected")
    async def protected(user=Depends(require_auth)):
        ...
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import get_settings

logger = logging.getLogger("falconconnect.auth.clerk")

# HTTPBearer with auto_error=False so we can give a better error message
security = HTTPBearer(auto_error=False)

# Clerk JWKS endpoint for JWT verification
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"


async def _verify_clerk_token(token: str) -> Dict[str, Any]:
    """Verify a Clerk session token via the Clerk Backend API.

    Uses the /sessions endpoint to verify the token. Returns user info
    on success, raises HTTPException on failure.
    """
    settings = get_settings()

    # Try to verify via Clerk's verify endpoint
    async with httpx.AsyncClient(timeout=10) as client:
        # Use the Clerk Backend API to verify the session token
        # The token from the frontend is a JWT — we verify it by calling
        # Clerk's /clients/verify endpoint or by decoding the JWT ourselves.
        # For simplicity and security, we use the Backend API.
        resp = await client.post(
            "https://api.clerk.com/v1/tokens/verify",
            headers={
                "Authorization": f"Bearer {settings.clerk_secret_key}",
                "Content-Type": "application/json",
            },
            json={"token": token},
        )

        if resp.status_code == 200:
            return resp.json()

        # Fallback: try the session-based approach
        # Clerk frontend sends session tokens as JWTs
        # We can also try to get the user from the token claims
        logger.warning("Clerk token verify returned %d, trying JWKS fallback", resp.status_code)

    # If Clerk verify fails, try JWKS-based JWT validation
    try:
        import jwt as pyjwt

        # Fetch JWKS
        async with httpx.AsyncClient(timeout=10) as client:
            jwks_resp = await client.get(
                CLERK_JWKS_URL,
                headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            )
            jwks_resp.raise_for_status()
            jwks = jwks_resp.json()

        # Decode the JWT
        # Get the signing key from JWKS
        header = pyjwt.get_unverified_header(token)
        kid = header.get("kid")

        signing_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                signing_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not signing_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find signing key for token",
            )

        claims = pyjwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return claims

    except ImportError:
        logger.warning("PyJWT not installed — cannot do JWKS-based verification")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
        )
    except Exception as e:
        logger.error("JWT verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Dict[str, Any]:
    """FastAPI dependency — require a valid Clerk session token.

    If CLERK_SECRET_KEY is empty (not yet configured), returns a placeholder
    user dict so the app can run in development mode. Logs a warning.

    In production with a real key, verifies the Bearer token against Clerk.
    """
    settings = get_settings()

    # If Clerk is not configured yet, allow access with a warning
    if not settings.clerk_secret_key:
        logger.warning(
            "CLERK_SECRET_KEY not configured — auth is DISABLED. "
            "Set CLERK_SECRET_KEY to enable authentication."
        )
        return {
            "user_id": "dev-mode",
            "email": "dev@falconconnect.local",
            "auth_mode": "disabled",
        }

    # Require a Bearer token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Use Bearer <clerk_session_token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_data = await _verify_clerk_token(token)
    return user_data
