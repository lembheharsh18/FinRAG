"""
Rate Limiting Middleware for FinRAG.

Uses slowapi to enforce per-route rate limits and prevent API abuse.
Limits are configurable via environment variables.
"""

import logging
from typing import Optional

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_rate_limit_key(request: Request) -> str:
    """
    Extract a rate-limit key from the request.

    Prefers the authenticated user ID (from the Authorization header)
    so that rate limits are per-user rather than per-IP behind proxies.
    Falls back to the client IP address.
    """
    # Try to use user identity from auth header (cheaper than decoding JWT)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Use a hash of the token as the key (don't store raw tokens)
        import hashlib

        token_hash = hashlib.sha256(auth_header.encode()).hexdigest()[:16]
        return f"user:{token_hash}"

    # Fallback to IP
    return get_remote_address(request)


# ── Global Limiter Instance ──────────────────────────────────────
limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=[settings.rate_limit_default],
    storage_uri="memory://",
)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """
    Custom handler for 429 Too Many Requests.

    Returns a JSON error with Retry-After header.
    """
    logger.warning(
        f"Rate limit exceeded: {exc.detail} — client: {_get_rate_limit_key(request)}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "detail": str(exc.detail),
        },
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )
