"""Simulator route tests — SIM-01 through SIM-05.

GET /api/simulator/calculate — validation endpoint (no Gemini, no Firestore writes).
All Firebase auth and calculator calls are mocked.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

from unittest.mock import MagicMock, patch
import pytest

_FAKE_UID = "sim-user-uid-999"
_FAKE_TOKEN = "sim.bearer.token"

_VALID_PARAMS = {
    "commute_mode": "metro",
    "avg_daily_km": 8.0,
    "diet_type": "vegetarian",
    "ac_hours_per_day": 2.0,
    "lpg_cylinders_per_month": 1.0,
}

_MOCK_BREAKDOWN = {
    "transport": 0.08,
    "diet": 2.5,
    "electricity": 2.46,
    "lpg": 0.4,
    "total": 5.44,
}


def _auth_headers():
    return {"Authorization": f"Bearer {_FAKE_TOKEN}"}


def _make_client():
    with patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}):
        from main import create_app
        from fastapi.testclient import TestClient
        return TestClient(create_app(), raise_server_exceptions=False)


# ── SIM-01 ────────────────────────────────────────────────────────────────────

def test_sim_01_valid_params_returns_score_and_breakdown():
    """SIM-01: GET /simulator/calculate valid params → 200, daily_co2_kg and breakdown."""
    mock_breakdown = dict(_MOCK_BREAKDOWN)
    mock_score = 5.44

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.simulator.calculate_daily_score", return_value=mock_score),
        patch("routes.simulator.calculate_breakdown", return_value=mock_breakdown),
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            "/api/simulator/calculate",
            params=_VALID_PARAMS,
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "daily_co2_kg" in body["data"]
    assert "breakdown" in body["data"]
    assert body["data"]["daily_co2_kg"] == mock_score


# ── SIM-02 ────────────────────────────────────────────────────────────────────

def test_sim_02_missing_param_returns_standard_error_shape():
    """SIM-02: GET /simulator/calculate missing required param → standard {success, data, error} shape.

    The response must always be wrapped in the standard format — never raw FastAPI 422.
    """
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        # Missing diet_type
        params = {k: v for k, v in _VALID_PARAMS.items() if k != "diet_type"}
        response = client.get(
            "/api/simulator/calculate",
            params=params,
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["error"], str)
    assert len(body["error"]) > 0
    # Must not contain raw Pydantic detail — always wrapped
    assert "detail" not in body
    assert "loc" not in body


# ── SIM-03 ────────────────────────────────────────────────────────────────────

def test_sim_03_unknown_commute_mode_returns_friendly_error():
    """SIM-03: Unknown commute_mode → standard {success: false} shape, friendly message.

    The response must always be the standard shape — never a raw error response.
    """
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        params = {**_VALID_PARAMS, "commute_mode": "helicopter"}
        response = client.get(
            "/api/simulator/calculate",
            params=params,
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["error"], str)
    assert len(body["error"]) > 0
    # Must not expose internals
    assert "Traceback" not in body["error"]
    assert "calculator.py" not in body["error"]
    assert "detail" not in body
    assert "loc" not in body


# ── SIM-04 ────────────────────────────────────────────────────────────────────

def test_sim_04_no_gemini_calls_ever():
    """SIM-04: Simulator route never calls AI — pure math only."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.simulator.calculate_daily_score", return_value=5.44),
        patch("routes.simulator.calculate_breakdown", return_value=_MOCK_BREAKDOWN),
        patch("ai_client.generate_content") as mock_ai,
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        client.get(
            "/api/simulator/calculate",
            params=_VALID_PARAMS,
            headers=_auth_headers(),
        )
        mock_ai.assert_not_called()


# ── SIM-05 ────────────────────────────────────────────────────────────────────

def test_sim_05_breakdown_has_required_keys():
    """SIM-05: Response breakdown has transport, diet, electricity, lpg, total keys."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.simulator.calculate_daily_score", return_value=5.44),
        patch("routes.simulator.calculate_breakdown", return_value=_MOCK_BREAKDOWN),
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            "/api/simulator/calculate",
            params=_VALID_PARAMS,
            headers=_auth_headers(),
        )

    body = response.json()
    breakdown = body["data"]["breakdown"]
    for key in ("transport", "diet", "electricity", "lpg", "total"):
        assert key in breakdown, f"Missing breakdown key: {key}"
