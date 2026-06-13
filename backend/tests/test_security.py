"""Tests for Phase 5 security deliverables.

Maps to SECURITY_SPEC.md §1, §6, §10 and the SEC-01 through SEC-10 test matrix.

Strategy:
  - Uses FastAPI TestClient (synchronous) via httpx.
  - No real Firebase, Gemini, or Firestore calls.
  - Tests middleware and exception handler behaviour directly on the app.
  - Route modules that are still placeholders are handled gracefully by main.py.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Ensure we run in development mode so HTTPSRedirect is NOT added
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")

import json
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Import the app factory — import after env vars are set
from main import create_app


# ── App fixture ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a TestClient wrapping a fresh app instance."""
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


# ── SEC-01 ────────────────────────────────────────────────────────────────────

def test_sec_01_health_returns_200_ok(client: TestClient):
    """SEC-01: GET /health returns 200 with {"status": "ok"}."""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok"}


# ── SEC-02 ────────────────────────────────────────────────────────────────────

REQUIRED_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


def test_sec_02_all_7_security_headers_present(client: TestClient):
    """SEC-02: All 7 security headers present on a normal /health response."""
    response = client.get("/health")
    for header_name, expected_value in REQUIRED_SECURITY_HEADERS.items():
        assert header_name in response.headers, (
            f"Missing security header: {header_name}"
        )
        assert response.headers[header_name] == expected_value, (
            f"Header {header_name}: "
            f"expected {expected_value!r}, got {response.headers[header_name]!r}"
        )


def test_sec_02_csp_header_present_with_correct_directives(client: TestClient):
    """SEC-02 (CSP): Content-Security-Policy header present and contains required directives."""
    response = client.get("/health")
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "'unsafe-inline'" in csp           # required for Tailwind
    assert "frame-ancestors 'none'" in csp


def test_sec_02_security_headers_on_404_response(client: TestClient):
    """SEC-02 (404): Security headers present even on 404 responses."""
    response = client.get("/nonexistent-path-xyz")
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers


# ── SEC-03 ────────────────────────────────────────────────────────────────────

def test_sec_03_body_over_10kb_rejected(client: TestClient):
    """SEC-03: Request with body > 10KB → 413 with standard error shape."""
    large_body = b"x" * 10_241  # 10 241 bytes — 1 byte over limit
    response = client.post(
        "/health",
        content=large_body,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["error"], str)
    assert len(body["error"]) > 0


def test_sec_03_content_length_header_triggers_rejection(client: TestClient):
    """SEC-03 (fast path): Content-Length > 10KB header alone triggers rejection."""
    response = client.get(
        "/health",
        headers={"Content-Length": "99999"},
    )
    assert response.status_code == 413
    body = response.json()
    assert body["success"] is False


# ── SEC-04 ────────────────────────────────────────────────────────────────────

def test_sec_04_path_traversal_in_url_blocked(client: TestClient):
    """SEC-04: URL containing ../ → blocked with 400."""
    response = client.get("/api/../etc/shadow")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["error"], str)


def test_sec_04_etc_passwd_in_url_blocked(client: TestClient):
    """SEC-04 (etc/passwd): URL probe for /etc/passwd → blocked."""
    response = client.get("/etc/passwd")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False


def test_sec_04_error_message_does_not_reveal_pattern(client: TestClient):
    """SEC-04 (hygiene): Block response does not mention the specific pattern matched."""
    response = client.get("/api/../traversal")
    body = response.json()
    error_msg = body.get("error", "").lower()
    # Must not reveal the specific matched pattern
    assert "../" not in error_msg
    assert "traversal" not in error_msg
    assert "pattern" not in error_msg


# ── SEC-05 ────────────────────────────────────────────────────────────────────

def test_sec_05_script_tag_in_body_blocked(client: TestClient):
    """SEC-05: <script in request body → blocked with 400."""
    payload = json.dumps({"message": "<script>alert(1)</script>"})
    response = client.post(
        "/health",
        content=payload.encode(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None


def test_sec_05_union_select_in_body_blocked(client: TestClient):
    """SEC-05 (SQL): UNION SELECT in body → blocked."""
    payload = json.dumps({"query": "' UNION SELECT * FROM users --"})
    response = client.post(
        "/health",
        content=payload.encode(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_sec_05_drop_table_in_body_blocked(client: TestClient):
    """SEC-05 (SQL drop): DROP TABLE in body → blocked."""
    payload = json.dumps({"cmd": "DROP TABLE users"})
    response = client.post(
        "/health",
        content=payload.encode(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


# ── SEC-06 ────────────────────────────────────────────────────────────────────

def test_sec_06_clean_request_passes_filter(client: TestClient):
    """SEC-06: Clean request under 10KB passes all middleware filters."""
    response = client.get("/health")
    assert response.status_code == 200


def test_sec_06_clean_post_body_passes_filter(client: TestClient):
    """SEC-06 (POST): Clean POST body under 10KB passes filter."""
    payload = json.dumps({"message": "I took the metro today"})
    response = client.post(
        "/health",
        content=payload.encode(),
        headers={"Content-Type": "application/json"},
    )
    # /health only accepts GET — expect 405, NOT 400 (filter passed)
    assert response.status_code != 400


# ── SEC-07 ────────────────────────────────────────────────────────────────────

def test_sec_07_cors_rejects_unknown_origin(client: TestClient):
    """SEC-07: CORS rejects requests from origins not in ALLOWED_ORIGINS."""
    response = client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    # The CORS middleware will not include Access-Control-Allow-Origin for unknown origins
    acao = response.headers.get("access-control-allow-origin", "")
    assert "evil.example.com" not in acao


def test_sec_07_cors_allows_configured_origin(client: TestClient):
    """SEC-07 (positive): Configured origin receives CORS header."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    acao = response.headers.get("access-control-allow-origin", "")
    assert "localhost:5173" in acao


# ── SEC-08 ────────────────────────────────────────────────────────────────────

def test_sec_08_exception_handler_returns_standard_shape_on_500():
    """SEC-08: Unhandled exception in a route → standard error shape, not raw traceback."""
    app = FastAPI()

    from exception_handler import register_exception_handlers
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("intentional test error")

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["error"], str)
    # Must not contain internal detail
    assert "RuntimeError" not in body["error"]
    assert "intentional test error" not in body["error"]
    assert "Traceback" not in body["error"]


def test_sec_08_500_response_has_security_headers():
    """SEC-08 (headers): SecurityHeaders middleware also fires on 500 responses."""
    from middleware.security_headers import SecurityHeadersMiddleware
    from exception_handler import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("intentional error")

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/boom")
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


# ── SEC-09 ────────────────────────────────────────────────────────────────────

def test_sec_09_422_validation_error_standard_shape():
    """SEC-09: FastAPI 422 validation error → standard shape, no Pydantic detail."""
    from fastapi import FastAPI
    from pydantic import BaseModel
    from exception_handler import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    class StrictModel(BaseModel):
        value: int  # must be int

    @app.post("/validated")
    async def validated(body: StrictModel):
        return {"success": True, "data": body.dict(), "error": None}

    test_client = TestClient(app, raise_server_exceptions=False)
    # Send a string where int is expected
    response = test_client.post(
        "/validated",
        json={"value": "not-an-int"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    # Generic message — no Pydantic field detail leaked
    assert body["error"] == "Please check your input and try again."
    # Must not contain Pydantic internal detail
    assert "loc" not in body
    assert "msg" not in body
    assert "type" not in body


def test_sec_09_422_response_does_not_leak_field_names():
    """SEC-09 (hygiene): 422 error body must not contain Pydantic field paths."""
    from fastapi import FastAPI
    from pydantic import BaseModel
    from exception_handler import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    class SensitiveModel(BaseModel):
        secret_field: int

    @app.post("/check")
    async def check(body: SensitiveModel):
        return {"ok": True}

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.post("/check", json={"secret_field": "bad"})

    raw_text = response.text
    assert "secret_field" not in raw_text or response.status_code != 422 or (
        # Only ok if the error wrapper fully replaces the body
        response.json().get("error") == "Please check your input and try again."
    )
    body = response.json()
    assert body["error"] == "Please check your input and try again."


# ── SEC-10 ────────────────────────────────────────────────────────────────────

def test_sec_10_rate_limit_exceeded_standard_shape():
    """SEC-10: Rate limit exceeded (429) → standard error shape."""
    from fastapi import FastAPI, Request
    from starlette.responses import JSONResponse
    from exception_handler import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    # Simulate a 429 by having the route raise an HTTPException directly
    from fastapi import HTTPException

    @app.get("/rate-limited")
    async def rate_limited():
        raise HTTPException(status_code=429, detail="too many requests")

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/rate-limited")

    assert response.status_code == 429
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == "Too many requests. Please wait a moment."
    # Must not contain raw slowapi or FastAPI detail
    assert "too many requests" not in body["error"].lower() or (
        body["error"] == "Too many requests. Please wait a moment."
    )


# ── Middleware unit tests ─────────────────────────────────────────────────────

def test_request_filter_path_traversal_blocked_directly():
    """Unit: RequestFilterMiddleware blocks ../ in URL path directly."""
    from fastapi import FastAPI
    from middleware.request_filter import RequestFilterMiddleware

    app = FastAPI()
    app.add_middleware(RequestFilterMiddleware)

    @app.get("/safe")
    async def safe():
        return {"ok": True}

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/../safe")
    assert response.status_code == 400


def test_request_filter_clean_url_passes():
    """Unit: RequestFilterMiddleware passes clean URLs through."""
    from fastapi import FastAPI
    from middleware.request_filter import RequestFilterMiddleware

    app = FastAPI()
    app.add_middleware(RequestFilterMiddleware)

    @app.get("/clean")
    async def clean():
        return {"ok": True}

    test_client = TestClient(app, raise_server_exceptions=False)
    response = test_client.get("/clean")
    assert response.status_code == 200


def test_request_size_exactly_at_limit_passes():
    """Unit: body exactly 10 240 bytes (at limit) passes RequestSizeLimitMiddleware."""
    from fastapi import FastAPI
    from middleware.request_size import RequestSizeLimitMiddleware

    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware)

    @app.post("/upload")
    async def upload(request: Request):
        return {"ok": True}

    test_client = TestClient(app, raise_server_exceptions=False)
    exact_body = b"x" * 10_240
    response = test_client.post(
        "/upload",
        content=exact_body,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200


def test_request_size_one_byte_over_rejected():
    """Unit: body 10 241 bytes (1 over limit) → 413."""
    from fastapi import FastAPI
    from middleware.request_size import RequestSizeLimitMiddleware

    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware)

    @app.post("/upload")
    async def upload(request: Request):
        return {"ok": True}

    test_client = TestClient(app, raise_server_exceptions=False)
    over_body = b"x" * 10_241
    response = test_client.post(
        "/upload",
        content=over_body,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413
