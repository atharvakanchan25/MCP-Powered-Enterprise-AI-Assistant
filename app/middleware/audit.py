import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        request_id = str(uuid.uuid4())[:8]

        response = await call_next(request)

        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "http.request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            client=request.client.host if request.client else "unknown",
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
