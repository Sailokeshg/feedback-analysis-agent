"""
Simple in-memory rate limiting middleware for development.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..config import settings


class InMemoryRateLimiter:
    """Simple in-memory rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        # Store: client_ip -> (tokens, last_refill_time)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (burst_limit, time.time())
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header first (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if there are multiple
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def is_allowed(self, request: Request) -> bool:
        """Check if request is allowed under rate limit."""
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        tokens, last_refill = self._buckets[client_ip]

        # Calculate tokens to add since last refill
        time_passed = current_time - last_refill
        tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
        tokens = min(self.burst_limit, tokens + tokens_to_add)

        # Check if we have enough tokens
        if tokens >= 1:
            tokens -= 1
            self._buckets[client_ip] = (tokens, current_time)
            return True
        else:
            self._buckets[client_ip] = (tokens, current_time)
            return False

    def get_remaining_tokens(self, request: Request) -> float:
        """Get remaining tokens for client."""
        client_ip = self._get_client_ip(request)
        tokens, _ = self._buckets[client_ip]
        return tokens


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    def __init__(self, app, rate_limiter: InMemoryRateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or InMemoryRateLimiter(
            requests_per_minute=settings.rate_limit.requests_per_minute,
            burst_limit=settings.rate_limit.burst_limit
        )

    async def dispatch(self, request: Request, call_next):
        """Process the request with rate limiting."""
        # Skip rate limiting if disabled
        if not settings.rate_limit.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks and docs
        if request.url.path in ["/healthz", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Check rate limit
        if not self.rate_limiter.is_allowed(request):
            # Calculate retry-after time
            remaining_tokens = self.rate_limiter.get_remaining_tokens(request)
            retry_after = int((1 - remaining_tokens) * 60 / settings.rate_limit.requests_per_minute)

            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(max(1, retry_after))}
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining_tokens = self.rate_limiter.get_remaining_tokens(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(remaining_tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response
