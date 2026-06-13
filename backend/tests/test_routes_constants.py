"""Constants route tests — RCONST-01 through RCONST-04.

Tests GET /api/constants — a public endpoint (no auth required).
No Firebase or Gemini mocking needed beyond suppressing the init check.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

from unittest.mock import MagicMock, patch
from constants.emission_factors import EMISSION_FACTORS


def _make_client():
    with patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}):
        from main import create_app
        from fastapi.testclient import TestClient
        return TestClient(create_app(), raise_server_exceptions=False)


# ── RCONST-01 ─────────────────────────────────────────────────────────────────

def test_rconst_01_get_constants_no_auth_returns_200():
    """RCONST-01: GET /api/constants — no auth header → 200 (public endpoint)."""
    client = _make_client()
    response = client.get("/api/constants")   # No Authorization header
    assert response.status_code == 200


# ── RCONST-02 ─────────────────────────────────────────────────────────────────

def test_rconst_02_response_has_success_true_and_constants_key():
    """RCONST-02: Response body has success: true and data.constants key."""
    client = _make_client()
    body = client.get("/api/constants").json()
    assert body["success"] is True
    assert body["data"] is not None
    assert "constants" in body["data"]


# ── RCONST-03 ─────────────────────────────────────────────────────────────────

def test_rconst_03_constants_value_matches_emission_factors():
    """RCONST-03: data.constants deep-equals EMISSION_FACTORS from emission_factors.py."""
    client = _make_client()
    constants = client.get("/api/constants").json()["data"]["constants"]
    assert constants == EMISSION_FACTORS


# ── RCONST-04 ─────────────────────────────────────────────────────────────────

def test_rconst_04_expired_token_still_returns_200():
    """RCONST-04: GET /api/constants with expired/invalid token still returns 200.

    /api/constants is a public endpoint — verify_token is NOT applied.
    An invalid Bearer token must not cause a 401.
    """
    client = _make_client()
    # Send a deliberately invalid token — should have no effect on this endpoint
    response = client.get(
        "/api/constants",
        headers={"Authorization": "Bearer expired.or.invalid.token"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
