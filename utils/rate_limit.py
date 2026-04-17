"""Shared slowapi rate-limiter.

Import `limiter` from this module in any router to apply rate limits, and
ensure `main.py` registers `app.state.limiter = limiter` + the exception
handler so FastAPI knows about it.

Key function prefers Cloudflare's CF-Connecting-IP, then X-Forwarded-For,
then falls back to the TCP peer address. falconverify sits behind
Cloudflare Pages, so raw peer IPs would collapse to edge addresses
without this.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _client_ip(request: Request) -> str:
    cf = request.headers.get("CF-Connecting-IP")
    if cf:
        return cf.strip()
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_client_ip)
