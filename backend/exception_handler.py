"""Global FastAPI exception handler — wraps all unhandled exceptions in the standard response format.

SECURITY: Never exposes stack traces, file paths, or class names to clients.
All internal detail is logged with logger.error(exc_info=True).

Standard response shape (always):
  {"success": false, "data": null, "error": "<generic message>"}
"""

# Standard library
import logging

# Third-party
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# ── Error message map — status code → external-safe message ──────────────────
# These strings are what the client receives. Nothing more.

_ERROR_MESSAGES: dict[int, str] = {
    401: "Authentication failed.",
    413: "Request too large.",
    422: "Please check your input and try again.",
    429: "Too many requests. Please wait a moment.",
    500: "Something went wrong. Please try again.",
}

_DEFAULT_ERROR_MESSAGE: str = "Something went wrong. Please try again."


def _error_response(message: str, status_code: int) -> JSONResponse:
    """Build the standard error JSON response.

    Args:
        message:     External-safe generic error message.
        status_code: HTTP status code for the response.

    Returns:
        JSONResponse with standard {success, data, error} shape.
    """
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "data": None, "error": message},
    )


def _get_message(status_code: int) -> str:
    """Look up the external-safe message for a given HTTP status code.

    Args:
        status_code: HTTP status code.

    Returns:
        Generic message string — never internal detail.
    """
    return _ERROR_MESSAGES.get(status_code, _DEFAULT_ERROR_MESSAGE)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle all HTTP exceptions (including 401, 413, 429) raised by FastAPI or middleware.

    Args:
        request: The incoming request.
        exc:     The StarletteHTTPException raised.

    Returns:
        Standard error JSONResponse.
    """
    try:
        message = _get_message(exc.status_code)
        if exc.status_code >= 500:
            logger.error(
                "HTTP %s on %s %s",
                exc.status_code, request.method, request.url.path,
                exc_info=True,
            )
        else:
            logger.warning(
                "HTTP %s on %s %s: %s",
                exc.status_code, request.method, request.url.path, exc.detail,
            )
        return _error_response(message, exc.status_code)
    except Exception:
        logger.error("Exception inside http_exception_handler", exc_info=True)
        return _error_response(_DEFAULT_ERROR_MESSAGE, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic RequestValidationError (FastAPI 422) — wraps in standard format.

    No Pydantic detail is forwarded to the client.

    Args:
        request: The incoming request.
        exc:     The RequestValidationError raised by Pydantic.

    Returns:
        Standard 422 error JSONResponse.
    """
    try:
        logger.warning(
            "Validation error on %s %s",
            request.method, request.url.path,
        )
        return _error_response(
            _ERROR_MESSAGES[422], status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except Exception:
        logger.error("Exception inside validation_exception_handler", exc_info=True)
        return _error_response(_DEFAULT_ERROR_MESSAGE, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler for any unhandled exception — logs detail, returns generic message.

    Args:
        request: The incoming request.
        exc:     Any unhandled exception.

    Returns:
        Standard 500 error JSONResponse.
    """
    try:
        logger.error(
            "Unhandled exception on %s %s",
            request.method, request.url.path,
            exc_info=True,
        )
        return _error_response(_DEFAULT_ERROR_MESSAGE, status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception:
        # Last-resort — if the handler itself fails
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "data": None, "error": _DEFAULT_ERROR_MESSAGE},
        )


def register_exception_handlers(app) -> None:  # type: ignore[no-untyped-def]
    """Register all exception handlers on the FastAPI app instance.

    Args:
        app: The FastAPI application instance.
    """
    try:
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        app.add_exception_handler(Exception, unhandled_exception_handler)
    except Exception as e:
        logger.error("Failed to register exception handlers: %s", e, exc_info=True)
        raise
