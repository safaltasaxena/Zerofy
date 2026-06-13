"""Request size limit middleware — rejects payloads over 10 KB.

SECURITY: Prevents memory exhaustion and oversized payload attacks.
Returns the standard error shape on rejection.
"""

# Standard library
import logging
from typing import Callable

# Third-party
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_MAX_BODY_SIZE_BYTES: int = 10_240        # 10 KB — from SECURITY_SPEC.md §10
_REJECT_STATUS_CODE: int = 413
_REJECT_ERROR_MESSAGE: str = "Request too large."


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that rejects request bodies exceeding _MAX_BODY_SIZE_BYTES.

    Reads the Content-Length header first for efficiency; falls back to reading
    the body if the header is absent (chunked transfer encoding, etc.).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request body size and reject if over the limit.

        Args:
            request:   The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            413 error response if body too large, otherwise the downstream response.
        """
        try:
            # Fast path — check Content-Length header before reading body
            content_length_header = request.headers.get("content-length")
            if content_length_header is not None:
                try:
                    declared_length = int(content_length_header)
                    if declared_length > _MAX_BODY_SIZE_BYTES:
                        logger.warning(
                            "RequestSizeLimit: rejected %s %s — "
                            "Content-Length %d > %d bytes",
                            request.method, request.url.path,
                            declared_length, _MAX_BODY_SIZE_BYTES,
                        )
                        return _reject_response()
                except ValueError:
                    pass  # Malformed header — let body read decide

            # Slow path — read and check actual body size
            body = await request.body()
            if len(body) > _MAX_BODY_SIZE_BYTES:
                logger.warning(
                    "RequestSizeLimit: rejected %s %s — body %d > %d bytes",
                    request.method, request.url.path,
                    len(body), _MAX_BODY_SIZE_BYTES,
                )
                return _reject_response()

            return await call_next(request)

        except Exception:
            raise


def _reject_response() -> JSONResponse:
    """Build the standard 413 rejection response.

    Returns:
        JSONResponse with standard error shape.
    """
    return JSONResponse(
        status_code=_REJECT_STATUS_CODE,
        content={"success": False, "data": None, "error": _REJECT_ERROR_MESSAGE},
    )
