"""FastAPI middleware for request tracing and structured logging."""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("empireo.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID into every request/response and log request details."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate or accept request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response else 500

            # Extract user_id from request state if set by auth dependency
            user_id = getattr(request.state, "user_id", None)

            logger.info(
                f"{request.method} {request.url.path} {status_code} {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "user_id": str(user_id) if user_id else None,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )

        # Attach request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
