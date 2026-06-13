"""Schema validation tests — SV-01 through SV-21.

Tests Pydantic model validation directly (no HTTP for SV-01–15)
and wrapping of HTTP error codes via TestClient (SV-16–21).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

import pytest
from pydantic import ValidationError
from unittest.mock import MagicMock, patch

from models.requests import OnboardingRequest, ChatUpdateRequest

# ── Valid baseline bodies ─────────────────────────────────────────────────────

_VALID_ONBOARDING = {
    "name": "Arjun Singh",
    "state": "Delhi",
    "city": "New Delhi",
    "commute_mode": "metro",
    "avg_daily_km": 12.0,
    "diet_type": "vegetarian",
    "ac_hours_per_day": 2.0,
    "lpg_cylinders_per_month": 1.0,
    "monthly_electricity_units": 200.0,
    "persona": "professional",
}


# ── SV-01 ─────────────────────────────────────────────────────────────────────

def test_sv_01_valid_onboarding_passes():
    """SV-01: OnboardingRequest — all valid fields → passes without error."""
    req = OnboardingRequest(**_VALID_ONBOARDING)
    assert req.name == "Arjun Singh"
    assert req.commute_mode == "metro"


# ── SV-02 ─────────────────────────────────────────────────────────────────────

def test_sv_02_avg_daily_km_over_500_raises():
    """SV-02: avg_daily_km = 501 → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "avg_daily_km": 501.0})


# ── SV-03 ─────────────────────────────────────────────────────────────────────

def test_sv_03_avg_daily_km_negative_raises():
    """SV-03: avg_daily_km = -1 → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "avg_daily_km": -1.0})


# ── SV-04 ─────────────────────────────────────────────────────────────────────

def test_sv_04_invalid_commute_mode_raises():
    """SV-04: commute_mode = 'helicopter' → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "commute_mode": "helicopter"})


# ── SV-05 ─────────────────────────────────────────────────────────────────────

def test_sv_05_invalid_diet_type_raises():
    """SV-05: diet_type = 'carnivore' → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "diet_type": "carnivore"})


# ── SV-06 ─────────────────────────────────────────────────────────────────────

def test_sv_06_empty_name_raises():
    """SV-06: name = '' (min_length=1) → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "name": ""})


# ── SV-07 ─────────────────────────────────────────────────────────────────────

def test_sv_07_name_200_chars_raises():
    """SV-07: name = 200-char string (max_length=100) → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "name": "A" * 200})


# ── SV-08 ─────────────────────────────────────────────────────────────────────

def test_sv_08_ac_hours_over_24_raises():
    """SV-08: ac_hours_per_day = 25 → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "ac_hours_per_day": 25.0})


# ── SV-09 ─────────────────────────────────────────────────────────────────────

def test_sv_09_lpg_over_10_raises():
    """SV-09: lpg_cylinders_per_month = 11 → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "lpg_cylinders_per_month": 11.0})


# ── SV-10 ─────────────────────────────────────────────────────────────────────

def test_sv_10_script_tag_in_message_raises():
    """SV-10: message = '<script>alert(1)</script>' → ValidationError (HTML validator)."""
    with pytest.raises(ValidationError):
        ChatUpdateRequest(message="<script>alert(1)</script>")


# ── SV-11 ─────────────────────────────────────────────────────────────────────

def test_sv_11_whitespace_only_message_raises():
    """SV-11: message = '   ' → ValidationError (whitespace stripped, then empty)."""
    with pytest.raises(ValidationError):
        ChatUpdateRequest(message="   ")


# ── SV-12 ─────────────────────────────────────────────────────────────────────

def test_sv_12_message_501_chars_raises():
    """SV-12: message = 501-char string → ValidationError (max_length=500)."""
    with pytest.raises(ValidationError):
        ChatUpdateRequest(message="x" * 501)


# ── SV-13 ─────────────────────────────────────────────────────────────────────

def test_sv_13_monthly_electricity_over_10000_raises():
    """SV-13: monthly_electricity_units = 10001 → ValidationError (le=10000)."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "monthly_electricity_units": 10001.0})


# ── SV-13b ───────────────────────────────────────────────────────────────────────────

def test_sv_13b_monthly_electricity_negative_raises():
    """SV-13b: monthly_electricity_units = -1 → ValidationError (ge=0)."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "monthly_electricity_units": -1.0})


# ── SV-14 ─────────────────────────────────────────────────────────────────────

def test_sv_14_invalid_persona_raises():
    """SV-14: persona = 'retiree' → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(**{**_VALID_ONBOARDING, "persona": "retiree"})


# ── SV-15 ─────────────────────────────────────────────────────────────────────

def test_sv_15_diesel_car_is_valid():
    """SV-15: commute_mode = 'diesel_car' → passes — valid enum value."""
    req = OnboardingRequest(**{**_VALID_ONBOARDING, "commute_mode": "diesel_car"})
    assert req.commute_mode == "diesel_car"


# ── Response shape tests (SV-16–21) via TestClient ───────────────────────────

def _make_test_client():
    """Build a minimal FastAPI TestClient with exception handlers registered."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from exception_handler import register_exception_handlers
    from models.requests import OnboardingRequest

    mini_app = FastAPI()
    register_exception_handlers(mini_app)

    @mini_app.post("/test/success")
    async def success_route():
        return {"success": True, "data": {"value": 42}, "error": None}

    @mini_app.post("/test/failure")
    async def failure_route():
        return {"success": False, "data": None, "error": "Something went wrong."}

    @mini_app.post("/test/validate")
    async def validate_route(body: OnboardingRequest):
        return {"success": True, "data": {}, "error": None}

    @mini_app.post("/test/crash")
    async def crash_route():
        raise ValueError("internal state corrupted at line 99 in calculator.py")

    return TestClient(mini_app, raise_server_exceptions=False)


# ── SV-16 ─────────────────────────────────────────────────────────────────────

def test_sv_16_success_response_shape():
    """SV-16: Any success → {success: true, data: {...}, error: null}."""
    client = _make_test_client()
    body = client.post("/test/success").json()
    assert body["success"] is True
    assert body["data"] is not None
    assert body["error"] is None


# ── SV-17 ─────────────────────────────────────────────────────────────────────

def test_sv_17_failure_response_shape():
    """SV-17: Any failure → {success: false, data: null, error: 'string'}."""
    client = _make_test_client()
    body = client.post("/test/failure").json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["error"], str)
    assert len(body["error"]) > 0


# ── SV-18 ─────────────────────────────────────────────────────────────────────

def test_sv_18_fastapi_422_wrapped_in_standard_format():
    """SV-18: FastAPI 422 validation error → wrapped in standard format."""
    client = _make_test_client()
    # Send invalid body — will trigger 422
    response = client.post("/test/validate", json={"name": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == "Please check your input and try again."
    # Must not contain raw Pydantic detail list
    assert "detail" not in body
    assert "loc" not in body


# ── SV-19 ─────────────────────────────────────────────────────────────────────

def test_sv_19_429_wrapped_with_correct_message():
    """SV-19: 429 rate limit → wrapped — 'Too many requests. Please wait a moment.'"""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from exception_handler import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/429")
    async def trigger_429():
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    client = TestClient(app, raise_server_exceptions=False)
    body = client.get("/test/429").json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == "Too many requests. Please wait a moment."


# ── SV-20 ─────────────────────────────────────────────────────────────────────

def test_sv_20_413_wrapped_with_correct_message():
    """SV-20: 413 request too large → wrapped — 'Request too large.'"""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from exception_handler import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/test/413")
    async def trigger_413():
        raise HTTPException(status_code=413, detail="payload too large")

    client = TestClient(app, raise_server_exceptions=False)
    body = client.post("/test/413").json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == "Request too large."


# ── SV-21 ─────────────────────────────────────────────────────────────────────

def test_sv_21_error_field_is_generic_no_stack_trace():
    """SV-21: error field is generic string — no stack trace, no file path."""
    client = _make_test_client()
    response = client.post("/test/crash")
    body = response.json()
    # Must not expose internals
    assert body["success"] is False
    error_str = body.get("error", "")
    assert "calculator.py" not in error_str
    assert "line 99" not in error_str
    assert "Traceback" not in error_str
    assert "ValueError" not in error_str
    assert isinstance(error_str, str)
    assert len(error_str) > 0
