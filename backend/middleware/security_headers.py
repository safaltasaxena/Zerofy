"""HTTP security headers middleware — adds all 7 headers from SECURITY_SPEC.md §1 to every response.

Applied as outermost middleware so every response, including error responses, carries these headers.
All header values are exact as specified — no environment variation.
"""

# Standard library
import os
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
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' data: https:; "
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
        if request.method == "OPTIONS":
            headers = dict(_SECURITY_HEADERS)
            origin = request.headers.get("origin")
            if origin:
                allowed_origins = [
                    o.strip()
                    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
                    if o.strip()
                ]
                
                # Check if origin is allowed (explicitly, localhost, or vercel.app)
                is_allowed = (
                    "*" in allowed_origins
                    or origin in allowed_origins
                    or origin.startswith("http://localhost:")
                    or origin.endswith(".vercel.app")
                )
                
                if is_allowed:
                    headers["Access-Control-Allow-Origin"] = origin
                    headers["Access-Control-Allow-Credentials"] = "true"
                else:
                    headers["Access-Control-Allow-Origin"] = allowed_origins[0] if allowed_origins else "http://localhost:5173"
                    headers["Access-Control-Allow-Credentials"] = "true"
            else:
                headers["Access-Control-Allow-Origin"] = "*"

            # Allow any methods and headers requested
            req_method = request.headers.get("access-control-request-method")
            headers["Access-Control-Allow-Methods"] = req_method if req_method else "GET, POST, PUT, DELETE, OPTIONS, PATCH"

            req_headers = request.headers.get("access-control-request-headers")
            headers["Access-Control-Allow-Headers"] = req_headers if req_headers else "Content-Type, Authorization, X-Requested-With"
            headers["Access-Control-Max-Age"] = "600"

            return Response(status_code=204, headers=headers)

        try:
            response: Response = await call_next(request)
        except Exception as e:
            from exception_handler import unhandled_exception_handler
            response = await unhandled_exception_handler(request, e)

        for header_name, header_value in _SECURITY_HEADERS.items():
            response.headers[header_name] = header_value
        return response
