"""Request filter middleware — blocks path traversal, XSS probes, and SQL injection attempts.

Checks both the URL path/query string and the raw request body.
Returns the standard error shape on block — never reveals which pattern matched.
SECURITY: Error message is generic so attackers cannot probe which patterns are blocked.
"""

# Standard library
import logging
import re
from typing import Callable

# Third-party
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# ── Blocked patterns — from SECURITY_SPEC.md §10 ─────────────────────────────
# Each is a compiled regex for performance. Case-insensitive matching is used
# where the threat is case-agnostic (SQL keywords, script tags).

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.\./"),                      # path traversal
    re.compile(r"etc/passwd"),                 # Unix passwd file probe
    re.compile(r"<script", re.IGNORECASE),     # XSS script tag
    re.compile(r"UNION\s+SELECT", re.IGNORECASE),  # SQL injection
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),    # SQL injection
]

_MAX_BODY_SCAN_BYTES: int = 10_240  # only scan up to 10KB — matches size limit
_BLOCK_STATUS_CODE: int = 400
_BLOCK_ERROR_MESSAGE: str = "Request contains invalid content."


def _contains_blocked_pattern(text: str) -> bool:
    """Check whether text matches any blocked pattern.

    Args:
        text: The string to scan (URL or body excerpt).

    Returns:
        True if any blocked pattern matches, False otherwise.
    """
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            return True
    return False


class RequestFilterMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that rejects requests containing dangerous patterns.

    Scans: URL path + query string, and the first _MAX_BODY_SCAN_BYTES of the body.
    On match: returns 400 with the standard error shape and logs a warning.
    Never reveals which pattern matched.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Inspect the request URL and body; block if a dangerous pattern is found.

        Args:
            request:   The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            400 error response if blocked, otherwise the downstream response.
        """
        try:
            # Check URL path + query string
            full_url = str(request.url)
            if _contains_blocked_pattern(full_url):
                logger.warning(
                    "RequestFilter: blocked request to %s (pattern in URL)",
                    request.url.path,
                )
                return _block_response()

            # Check request body — read and cache it so downstream can still read it
            body_bytes = await request.body()
            body_sample = body_bytes[:_MAX_BODY_SCAN_BYTES].decode("utf-8", errors="replace")
            if _contains_blocked_pattern(body_sample):
                logger.warning(
                    "RequestFilter: blocked request to %s (pattern in body)",
                    request.url.path,
                )
                return _block_response()

            return await call_next(request)

        except Exception:
            raise


def _block_response() -> JSONResponse:
    """Build the standard 400 block response.

    Returns:
        JSONResponse with standard error shape and generic message.
    """
    return JSONResponse(
        status_code=_BLOCK_STATUS_CODE,
        content={"success": False, "data": None, "error": _BLOCK_ERROR_MESSAGE},
    )
