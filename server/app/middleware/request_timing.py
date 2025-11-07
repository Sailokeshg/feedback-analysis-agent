"""
Request timing middleware with structured logging and request ID generation.
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ..logging import log, set_request_context, clear_request_context


class RequestTimingMiddleware:
    """Middleware for request timing, logging, and request ID generation."""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Start timing
        start_time = time.time()

        # Set request context
        try:
            set_request_context(request_id_val=request_id)
        except Exception:
            # Context setting failed, continue without it
            pass

        # Create request object for logging
        request = Request(scope, receive)

        # Log request start
        log.info(
            "Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
            }
        )

        # Process request
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            log.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                    "status_code": 500,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise
        finally:
            # Clear request context
            try:
                clear_request_context()
            except Exception:
                # Context clearing failed, continue
                pass

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request headers."""
        # Check X-Forwarded-For header first (for proxies/load balancers)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # Take the first IP if there are multiple
            return x_forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip

        # Fall back to direct connection
        client = request.client
        return client.host if client else "unknown"


def create_timing_middleware(app):
    """Create and return the request timing middleware."""
    return RequestTimingMiddleware(app)


# Response logging middleware (separate for better separation of concerns)
class ResponseLoggingMiddleware:
    """Middleware for logging response details."""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Intercept send to capture response
        original_send = send
        response_data = {"status_code": 200, "headers": {}}

        async def logging_send(message):
            if message["type"] == "http.response.start":
                response_data["status_code"] = message["status"]
                response_data["headers"] = dict(message.get("headers", []))
            elif message["type"] == "http.response.body":
                # We could capture response size here if needed
                pass

            await original_send(message)

        await self.app(scope, receive, logging_send)

        # Log response (this will be called after the response is sent)
        # Note: This is a simplified version. In practice, you'd want to
        # coordinate with the request timing middleware to include duration.


def log_request_complete(
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    response_size: int = 0,
    **extra
):
    """Log completed request with timing information."""
    level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"

    log.log(
        level,
        "Request completed",
        extra={
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size_bytes": response_size,
            **extra,
        }
    )
