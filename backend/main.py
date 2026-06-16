"""FastAPI application entry point — registers all routers, middleware, and exception handlers.

Middleware registration order (add_middleware is LIFO — last added = outermost):
  Added first  → innermost (first to process request, last to process response)
  Added last   → outermost (last to process request, first to process response)

Desired request pipeline per SECURITY_SPEC.md §10:
  [outermost] SecurityHeaders → CORS → HTTPS → SizeLimit → RequestFilter → RateLimit [innermost]

Therefore add_middleware calls are in this order:
  1. RateLimitMiddleware      (innermost — added first)
  2. RequestFilterMiddleware
  3. RequestSizeLimitMiddleware
  4. HTTPSRedirectMiddleware  (production only)
  5. CORSMiddleware
  6. SecurityHeadersMiddleware (outermost — added last)
"""

# Standard library
import logging
import os

# Third-party
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Internal — middleware
from middleware.rate_limiter import limiter
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.request_filter import RequestFilterMiddleware
from middleware.request_size import RequestSizeLimitMiddleware

# Internal — exception handlers
from exception_handler import register_exception_handlers

# Internal — routers: all routes complete — direct imports
from routes import user
from routes import logs
from routes import simulator
from routes import quiz
from routes import gamification
from routes import constants as constants_route

load_dotenv()

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_APP_TITLE: str = "Zerofy India API"
_APP_VERSION: str = "1.0.0"
_HEALTH_STATUS: dict[str, str] = {"status": "ok"}
_ALLOWED_METHODS: list[str] = ["GET", "POST", "PUT"]
_ALLOWED_HEADERS: list[str] = ["Content-Type", "Authorization"]



# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Registers exception handlers, middleware (in correct LIFO order),
    and all route routers.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=_APP_TITLE,
        version=_APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Attach the slowapi limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Register custom exception handlers
    register_exception_handlers(app)

    # ── Middleware — add in LIFO order (innermost first, outermost last) ──────

    # [1] RateLimitMiddleware — innermost (closest to route handlers)
    # slowapi works via decorator on routes; no add_middleware call needed here.
    # The limiter is attached to app.state above.

    # [2] RequestFilterMiddleware
    app.add_middleware(RequestFilterMiddleware)

    # [3] RequestSizeLimitMiddleware
    app.add_middleware(RequestSizeLimitMiddleware)

    # [4] HTTPSRedirectMiddleware — production only
    if os.getenv("ENVIRONMENT", "development") == "production":
        app.add_middleware(HTTPSRedirectMiddleware)

    # [5] CORSMiddleware
    allowed_origins = _parse_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=_ALLOWED_METHODS,
        allow_headers=_ALLOWED_HEADERS,
    )

    # [6] SecurityHeadersMiddleware — outermost (added last)
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    _register_routers(app)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Public health check endpoint — no auth required.

        Returns:
            {"status": "ok"} when the service is running.
        """
        return _HEALTH_STATUS

    return app


def _parse_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS env variable into a list of origin strings.

    Expects a comma-separated string, e.g.:
      "http://localhost:5173,https://zerofy.in"

    Returns:
        List of origin strings. Falls back to localhost if env var is absent.
    """
    try:
        raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        return [o.strip() for o in raw.split(",") if o.strip()]
    except Exception as e:
        logger.error("Failed to parse ALLOWED_ORIGINS: %s", e, exc_info=True)
        return ["http://localhost:5173"]


def _register_routers(app: FastAPI) -> None:
    """Include all API routers with the /api prefix.

    All 6 route modules are complete as of Phase 8 — registered directly.

    Args:
        app: The FastAPI application instance.
    """
    try:
        app.include_router(user.router, prefix="/api")
        app.include_router(constants_route.router, prefix="/api")
        app.include_router(logs.router, prefix="/api")
        app.include_router(simulator.router, prefix="/api")
        app.include_router(quiz.router, prefix="/api")
        app.include_router(gamification.router, prefix="/api")
    except Exception as e:
        logger.error("Failed to register routers: %s", e, exc_info=True)
        raise


# ── Application instance ──────────────────────────────────────────────────────

app = create_app()
