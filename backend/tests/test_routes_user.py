"""Tests for routes/user.py and routes/constants.py.

Maps to USER-01 through USER-10 test matrix.

Mocking strategy:
  - firebase_admin.auth.verify_id_token → patched to return a fake decoded token.
  - config.firebase.get_db → patched to return a mock Firestore client.
  - No real Firebase, Firestore, or Gemini calls in any test.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Prevent firebase_admin from attempting real initialisation on import
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from constants.emission_factors import EMISSION_FACTORS

# ── Fixtures ──────────────────────────────────────────────────────────────────

_FAKE_UID = "test-user-uid-12345"
_FAKE_TOKEN = "fake.firebase.token"

_VALID_ONBOARDING_BODY = {
    "name": "Priya Sharma",
    "state": "Maharashtra",
    "city": "Mumbai",
    "commute_mode": "metro",
    "avg_daily_km": 8.0,
    "diet_type": "vegetarian",
    "ac_hours_per_day": 2.0,
    "lpg_cylinders_per_month": 1.0,
    "persona": "professional",
}

_SAVED_PROFILE = {
    "name": "Priya Sharma",
    "state": "Maharashtra",
    "city": "Mumbai",
    "commute_mode": "metro",
    "avg_daily_km": 8.0,
    "diet_type": "vegetarian",
    "ac_hours_per_day": 2.0,
    "lpg_cylinders_per_month": 1.0,
    "persona": "professional",
}


def _mock_verify_token(uid: str = _FAKE_UID):
    """Return a patch target that makes verify_id_token return a decoded token dict."""
    return {"uid": uid}


def _mock_firestore_doc(data: dict | None):
    """Build a mock Firestore DocumentSnapshot."""
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data
    return doc


def _make_mock_db(doc_data: dict | None = _SAVED_PROFILE) -> MagicMock:
    """Build a mock Firestore client whose collection().document().get() returns doc_data."""
    db = MagicMock()
    doc_ref = MagicMock()
    doc_ref.get.return_value = _mock_firestore_doc(doc_data)
    doc_ref.set.return_value = None
    db.collection.return_value.document.return_value = doc_ref
    return db


@pytest.fixture(scope="function")
def client():
    """TestClient with Firebase auth and Firestore fully mocked."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("config.firebase.get_db", return_value=_make_mock_db()),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        # Import app after patching to avoid real Firebase init
        from main import create_app
        app = create_app()
        yield TestClient(app, raise_server_exceptions=False)


def _auth_headers() -> dict:
    """Return Authorization header with a fake Bearer token."""
    return {"Authorization": f"Bearer {_FAKE_TOKEN}"}


# ── USER-01 ───────────────────────────────────────────────────────────────────

def test_user_01_onboarding_valid_body_returns_200_with_score(client):
    """USER-01: POST /onboarding with valid body → 200, daily_co2_kg, profile returned."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("routes.user.get_db", return_value=_make_mock_db()),
    ):
        response = client.post(
            "/api/user/onboarding",
            json=_VALID_ONBOARDING_BODY,
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "daily_co2_kg" in body["data"]
    assert "profile" in body["data"]
    assert isinstance(body["data"]["daily_co2_kg"], float)


# ── USER-02 ───────────────────────────────────────────────────────────────────

def test_user_02_onboarding_missing_required_field_returns_422(client):
    """USER-02: POST /onboarding with missing field → 422, standard error shape, no Pydantic detail."""
    with patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()):
        body_missing_name = {k: v for k, v in _VALID_ONBOARDING_BODY.items() if k != "name"}
        response = client.post(
            "/api/user/onboarding",
            json=body_missing_name,
            headers=_auth_headers(),
        )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == "Please check your input and try again."
    # Must not contain raw Pydantic detail fields
    assert "loc" not in body
    assert "msg" not in body


# ── USER-03 ───────────────────────────────────────────────────────────────────

def test_user_03_onboarding_invalid_commute_mode_returns_422(client):
    """USER-03: POST /onboarding with invalid commute_mode → 422, standard shape."""
    with patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()):
        bad_body = {**_VALID_ONBOARDING_BODY, "commute_mode": "helicopter"}
        response = client.post(
            "/api/user/onboarding",
            json=bad_body,
            headers=_auth_headers(),
        )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"] == "Please check your input and try again."


def test_user_03_invalid_diet_type_returns_422(client):
    """USER-03 (variant): invalid diet_type → 422."""
    with patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()):
        bad_body = {**_VALID_ONBOARDING_BODY, "diet_type": "carnivore"}
        response = client.post(
            "/api/user/onboarding",
            json=bad_body,
            headers=_auth_headers(),
        )

    assert response.status_code == 422


# ── USER-04 ───────────────────────────────────────────────────────────────────

def test_user_04_get_profile_valid_token_returns_profile(client):
    """USER-04: GET /profile with valid token → 200, profile in response."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("routes.user.get_db", return_value=_make_mock_db(_SAVED_PROFILE)),
    ):
        response = client.get("/api/user/profile", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "profile" in body["data"]
    assert body["data"]["profile"]["name"] == "Priya Sharma"


# ── USER-05 ───────────────────────────────────────────────────────────────────

def test_user_05_get_profile_no_token_returns_401(client):
    """USER-05: GET /profile with no Authorization header → 401."""
    response = client.get("/api/user/profile")
    assert response.status_code == 401


def test_user_05_get_profile_invalid_token_returns_401(client):
    """USER-05 (invalid token): invalid Bearer token → 401."""
    import firebase_admin.auth
    with patch(
        "firebase_admin.auth.verify_id_token",
        side_effect=firebase_admin.auth.InvalidIdTokenError("bad token"),
    ):
        response = client.get(
            "/api/user/profile",
            headers={"Authorization": "Bearer bad.token.here"},
        )
    assert response.status_code == 401


# ── USER-06 ───────────────────────────────────────────────────────────────────

def test_user_06_put_profile_partial_update_merges_correctly(client):
    """USER-06: PUT /profile with partial update → 200, merged profile, recalculated score."""
    existing = dict(_SAVED_PROFILE)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("routes.user.get_db", return_value=_make_mock_db(existing)),
    ):
        partial = {"diet_type": "vegan", "ac_hours_per_day": 0.0}
        response = client.put(
            "/api/user/profile",
            json=partial,
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["profile"]["diet_type"] == "vegan"
    assert body["data"]["profile"]["ac_hours_per_day"] == 0.0
    # Unchanged fields must still be present
    assert body["data"]["profile"]["commute_mode"] == "metro"
    assert "daily_co2_kg" in body["data"]


def test_user_06_put_profile_non_updated_fields_preserved(client):
    """USER-06 (preservation): PUT with one field update — other fields unchanged."""
    existing = dict(_SAVED_PROFILE)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("routes.user.get_db", return_value=_make_mock_db(existing)),
    ):
        response = client.put(
            "/api/user/profile",
            json={"avg_daily_km": 12.0},
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["data"]["profile"]["avg_daily_km"] == 12.0
    assert body["data"]["profile"]["diet_type"] == "vegetarian"  # unchanged
    assert body["data"]["profile"]["name"] == "Priya Sharma"     # unchanged


# ── USER-07 ───────────────────────────────────────────────────────────────────

def test_user_07_get_constants_no_auth_returns_200(client):
    """USER-07: GET /constants — no auth required → 200, returns emission factors."""
    response = client.get("/api/constants")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "constants" in body["data"]


def test_user_07_get_constants_ignores_auth_header(client):
    """USER-07 (no token needed): GET /constants works without Authorization header."""
    response = client.get("/api/constants")
    # Should succeed regardless of auth
    assert response.status_code == 200


# ── USER-08 ───────────────────────────────────────────────────────────────────

def test_user_08_constants_has_all_required_top_level_keys(client):
    """USER-08: GET /constants data has transport, diet, electricity, lpg keys."""
    response = client.get("/api/constants")
    constants = response.json()["data"]["constants"]
    assert "transport" in constants
    assert "diet" in constants
    assert "electricity" in constants
    assert "lpg" in constants


def test_user_08_constants_transport_includes_metro(client):
    """USER-08 (structure): transport section includes metro."""
    response = client.get("/api/constants")
    constants = response.json()["data"]["constants"]
    assert "metro" in constants["transport"]
    assert "petrol_car" in constants["transport"]


def test_user_08_constants_matches_emission_factors(client):
    """USER-08 (fidelity): returned constants match EMISSION_FACTORS exactly."""
    response = client.get("/api/constants")
    returned = response.json()["data"]["constants"]
    assert returned["transport"] == EMISSION_FACTORS["transport"]
    assert returned["diet"] == EMISSION_FACTORS["diet"]
    assert returned["electricity"] == EMISSION_FACTORS["electricity"]
    assert returned["lpg"] == EMISSION_FACTORS["lpg"]


# ── USER-09 ───────────────────────────────────────────────────────────────────

def test_user_09_onboarding_saves_to_correct_firestore_path(client):
    """USER-09: POST /onboarding saves to profiles/{user_id} in Firestore."""
    mock_db = _make_mock_db()

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("routes.user.get_db", return_value=mock_db),
    ):
        response = client.post(
            "/api/user/onboarding",
            json=_VALID_ONBOARDING_BODY,
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    # Verify Firestore was called with the correct collection and document ID
    mock_db.collection.assert_called_with("profiles")
    mock_db.collection.return_value.document.assert_called_with(_FAKE_UID)
    mock_db.collection.return_value.document.return_value.set.assert_called_once()


# ── USER-10 ───────────────────────────────────────────────────────────────────

def test_user_10_user_id_from_token_not_from_body(client):
    """USER-10: user_id comes from verified token uid — never from request body."""
    attacker_uid = "attacker-uid-9999"
    real_uid = _FAKE_UID
    mock_db = _make_mock_db()

    # Even if attacker sends a user_id field in the body, the token uid is used
    body_with_injected_uid = {
        **_VALID_ONBOARDING_BODY,
        "user_id": attacker_uid,   # should be completely ignored
    }

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token(real_uid)),
        patch("routes.user.get_db", return_value=mock_db),
    ):
        response = client.post(
            "/api/user/onboarding",
            json=body_with_injected_uid,
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    # The document must have been saved under the real_uid — not the attacker's uid
    mock_db.collection.return_value.document.assert_called_with(real_uid)
    # Verify document was NOT created for the attacker uid
    calls = mock_db.collection.return_value.document.call_args_list
    called_uids = [c.args[0] for c in calls]
    assert attacker_uid not in called_uids


def test_user_10_profile_uid_from_token_not_from_query_param(client):
    """USER-10 (GET): uid from token, not from query parameters."""
    mock_db = _make_mock_db(_SAVED_PROFILE)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token(_FAKE_UID)),
        patch("routes.user.get_db", return_value=mock_db),
    ):
        # Even with an attacker uid in the query, the token uid is used
        response = client.get(
            "/api/user/profile?user_id=hacker-uid",
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    mock_db.collection.return_value.document.assert_called_with(_FAKE_UID)


# ── Additional edge cases ─────────────────────────────────────────────────────

def test_get_profile_returns_404_shape_when_not_found(client):
    """Graceful 200 with error message when profile does not exist in Firestore."""
    mock_db = _make_mock_db(None)  # doc.exists = False

    with (
        patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()),
        patch("routes.user.get_db", return_value=mock_db),
    ):
        response = client.get("/api/user/profile", headers=_auth_headers())

    # Route returns standard shape — not a 404 HTTP exception
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert "not found" in body["error"].lower() or "onboarding" in body["error"].lower()


def test_onboarding_avg_daily_km_over_500_returns_422(client):
    """avg_daily_km > 500 → 422 from Pydantic, standard error shape."""
    with patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()):
        bad_body = {**_VALID_ONBOARDING_BODY, "avg_daily_km": 999.0}
        response = client.post(
            "/api/user/onboarding",
            json=bad_body,
            headers=_auth_headers(),
        )
    assert response.status_code == 422
    assert response.json()["error"] == "Please check your input and try again."


def test_onboarding_ac_hours_over_24_returns_422(client):
    """ac_hours_per_day > 24 → 422 from Pydantic, standard error shape."""
    with patch("firebase_admin.auth.verify_id_token", return_value=_mock_verify_token()):
        bad_body = {**_VALID_ONBOARDING_BODY, "ac_hours_per_day": 25.0}
        response = client.post(
            "/api/user/onboarding",
            json=bad_body,
            headers=_auth_headers(),
        )
    assert response.status_code == 422
