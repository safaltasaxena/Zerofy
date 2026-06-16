"""HTTP security headers middleware — adds all 7 headers from SECURITY_SPEC.md §1 to every response.

Applied as outermost middleware so every response, including error responses, carries these headers.
All header values are exact as specified — no environment variation.
"""

# Standard library
from typing import Callable

# Third-party
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# ── Header constants — exact values from SECURITY_SPEC.md §1 ─────────────────

_HEADER_X_CONTENT_TYPE_OPTIONS: str = "nosniff"
_HEADER_X_FRAME_OPTIONS: str = "DENY"
_HEADER_X_XSS_PROTECTION: str = "1; mode=block"
_HEADER_REFERRER_POLICY: str = "strict-origin-when-cross-origin"
_HEADER_PERMISSIONS_POLICY: str = "geolocation=(), microphone=(), camera=()"
_HEADER_HSTS: str = "max-age=63072000; includeSubDomains"
_HEADER_CSP: str = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self' https://generativelanguage.googleapis.com; "
    "frame-ancestors 'none'"
)

_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": _HEADER_X_CONTENT_TYPE_OPTIONS,
    "X-Frame-Options": _HEADER_X_FRAME_OPTIONS,
    "X-XSS-Protection": _HEADER_X_XSS_PROTECTION,
    "Referrer-Policy": _HEADER_REFERRER_POLICY,
    "Permissions-Policy": _HEADER_PERMISSIONS_POLICY,
    "Strict-Transport-Security": _HEADER_HSTS,
    "Content-Security-Policy": _HEADER_CSP,
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that appends all 7 HTTP security headers to every response.

    Applied once globally in main.py — never per-route.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and attach security headers to the response.

        Args:
            request:   The incoming HTTP request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            The response with all security headers attached.
        """
        try:
            response: Response = await call_next(request)
        except Exception as e:
            from exception_handler import unhandled_exception_handler
            response = await unhandled_exception_handler(request, e)

        for header_name, header_value in _SECURITY_HEADERS.items():
            response.headers[header_name] = header_value
        return response
