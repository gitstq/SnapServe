"""
API key authentication and rate limiting middleware.
"""

import hashlib
import logging
import time
from collections import defaultdict
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check if a request is allowed under the rate limit.

        Returns:
            Tuple of (is_allowed, remaining_requests).
        """
        now = time.time()
        window_start = now - self._window_seconds

        # Clean old entries
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > window_start
        ]

        if len(self._requests[key]) >= self._max_requests:
            return False, 0

        self._requests[key].append(now)
        remaining = self._max_requests - len(self._requests[key])
        return True, remaining

    def cleanup(self) -> None:
        """Remove expired entries."""
        now = time.time()
        window_start = now - self._window_seconds
        expired_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < window_start
        ]
        for key in expired_keys:
            del self._requests[key]


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, api_key: Optional[str] = None, header_name: str = "X-API-Key"):
        self._api_key = api_key
        self._header_name = header_name

        if api_key:
            # Store hashed version for security
            self._hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
        else:
            self._hashed_key = None

    def is_auth_enabled(self) -> bool:
        """Check if API key authentication is enabled."""
        return self._api_key is not None

    def validate(self, request: Request) -> bool:
        """
        Validate the API key from the request.

        Returns True if authentication is disabled or key is valid.
        """
        if not self.is_auth_enabled():
            return True

        provided_key = request.headers.get(self._header_name, "")

        # Also check query parameter
        if not provided_key:
            provided_key = request.query_params.get("api_key", "")

        if not provided_key:
            return False

        hashed_provided = hashlib.sha256(provided_key.encode()).hexdigest()
        return hashed_provided == self._hashed_key


class AuthMiddleware(BaseHTTPMiddleware):
    """Combined authentication and rate limiting middleware."""

    # Paths that don't require authentication
    PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self._auth = APIKeyAuth(
            api_key=settings.api_key,
            header_name=settings.api_key_header,
        )
        self._rate_limiter = RateLimiter(
            max_requests=settings.rate_limit_per_minute,
            window_seconds=60,
        )

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Check API key
        if self._auth.is_auth_enabled():
            if not self._auth.validate(request):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Unauthorized",
                        "message": "Invalid or missing API key. "
                                   f"Provide it via '{get_settings().api_key_header}' header.",
                    },
                )

        # Rate limiting
        client_key = request.client.host if request.client else "unknown"
        if self._auth.is_auth_enabled():
            api_key = request.headers.get(get_settings().api_key_header, "")
            client_key = f"{client_key}:{hashlib.md5(api_key.encode()).hexdigest()[:8]}"

        allowed, remaining = self._rate_limiter.is_allowed(client_key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
