"""Security headers middleware — applies HSTS / nosniff / framing / referrer /
permissions-policy to every response. Deliberately no CSP here: we ship a
bundled frontend from this service and a CSP needs per-route tuning (the
falconverify SPA gets its CSP via Cloudflare Pages `_headers` instead).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware


_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        for k, v in _HEADERS.items():
            response.headers.setdefault(k, v)
        return response
