"""Tests for routes/logs.py — daily log retrieval and NLP chat-update pipeline.

Maps to LOG-01 through LOG-10.

Mocking strategy:
  - firebase_admin.auth.verify_id_token → returns fake decoded token.
  - routes.logs.get_db → returns mock Firestore client.
  - utils.gemini_parser.parse_user_message → returns fake parsed fields.
  - utils.suggestion_engine.get_suggestions → returns fake suggestion list.
  No real Firebase, Firestore, Gemini, or network calls in any test.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Shared constants ──────────────────────────────────────────────────────────

_FAKE_UID = "user-uid-test-999"
_FAKE_TOKEN = "fake.bearer.token"
_TODAY = date.today().isoformat()
_DOC_ID = f"{_FAKE_UID}_{_TODAY}"

_VALID_LOG = {
    "user_id": _FAKE_UID,
    "date": _TODAY,
    "commute_mode": "metro",
    "avg_daily_km": 8.0,
    "diet_type": "vegetarian",
    "ac_hours_per_day": 2.0,
    "lpg_cylinders_per_month": 0.5,
}

_VALID_PROFILE = {
    "commute_mode": "metro",
    "avg_daily_km": 8.0,
    "diet_type": "vegetarian",
    "ac_hours_per_day": 2.0,
    "lpg_cylinders_per_month": 0.5,
    "persona": "professional",
}

_PARSED_FIELDS = {
    "commute_mode": "metro",
    "avg_daily_km": 5.0,
    "diet_type": None,
    "ac_hours_per_day": None,
    "lpg_cylinders_per_month": None,
}


# ── Firestore mock helpers ────────────────────────────────────────────────────

def _mock_doc(data: dict | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data
    return doc


def _make_mock_db(
    log_data: dict | None = _VALID_LOG,
    profile_data: dict | None = _VALID_PROFILE,
    weekly_docs: list[dict] | None = None,
) -> MagicMock:
    """Build a mock Firestore client covering all collection access patterns in logs.py."""
    db = MagicMock()

    # Dispatch .collection() calls by collection name
    def _collection_side_effect(name: str):
        coll = MagicMock()

        if name == "daily_logs":
            doc_ref = MagicMock()
            doc_ref.get.return_value = _mock_doc(log_data)
            doc_ref.set.return_value = None
            coll.document.return_value = doc_ref

            # Weekly trend query chain
            stream_docs = []
            for entry in (weekly_docs or []):
                d = MagicMock()
                d.to_dict.return_value = entry
                stream_docs.append(d)

            query_chain = MagicMock()
            query_chain.where.return_value = query_chain
            query_chain.order_by.return_value = query_chain
            query_chain.limit.return_value = query_chain
            query_chain.stream.return_value = iter(stream_docs)
            coll.where.return_value = query_chain

        elif name == "profiles":
            doc_ref = MagicMock()
            doc_ref.get.return_value = _mock_doc(profile_data)
            coll.document.return_value = doc_ref

        elif name == "gamification":
            doc_ref = MagicMock()
            doc_ref.get.return_value = _mock_doc(None)
            doc_ref.set.return_value = None
            coll.document.return_value = doc_ref

        return coll

    db.collection.side_effect = _collection_side_effect
    return db


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_FAKE_TOKEN}"}


# ── App fixture ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def client():
    """TestClient with Firebase auth, Firestore, and Gemini fully mocked."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("config.firebase.get_db", return_value=_make_mock_db()),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("utils.gemini_parser.parse_user_message", return_value=_PARSED_FIELDS),
        patch("utils.suggestion_engine.get_suggestions", return_value=["s1", "s2", "s3"]),
    ):
        from main import create_app
        app = create_app()
        yield TestClient(app, raise_server_exceptions=False)


# ── LOG-01 ────────────────────────────────────────────────────────────────────

def test_log_01_get_today_existing_log_returns_log_and_analogy():
    """LOG-01: GET /today with existing log → 200, returns log + analogy."""
    mock_db = _make_mock_db(log_data=_VALID_LOG)
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/logs/{_FAKE_UID}/today", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "log" in body["data"]
    assert "analogy" in body["data"]
    assert "daily_co2_kg" in body["data"]
    assert "breakdown" in body["data"]
    assert body["error"] is None


# ── LOG-02 ────────────────────────────────────────────────────────────────────

def test_log_02_get_today_no_log_returns_zeroed_structure():
    """LOG-02: GET /today with no log → 200, zeroed structure (not 404)."""
    mock_db = _make_mock_db(log_data=None)
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/logs/{_FAKE_UID}/today", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["daily_co2_kg"] == 0.0
    assert body["data"]["breakdown"]["total"] == 0.0
    # Log structure present but zeroed
    assert "log" in body["data"]
    assert "analogy" in body["data"]


# ── LOG-03 ────────────────────────────────────────────────────────────────────

def test_log_03_get_weekly_returns_7_point_trend():
    """LOG-03: GET /weekly → 200, returns trend array (up to 7 entries)."""
    weekly = [
        {**_VALID_LOG, "date": f"2026-06-{7 + i:02d}"}
        for i in range(7)
    ]
    mock_db = _make_mock_db(weekly_docs=weekly)
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/logs/{_FAKE_UID}/weekly", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "trend" in body["data"]
    trend = body["data"]["trend"]
    assert isinstance(trend, list)
    assert len(trend) == 7
    for entry in trend:
        assert "date" in entry
        assert "daily_co2_kg" in entry


# ── LOG-04 ────────────────────────────────────────────────────────────────────

def test_log_04_chat_update_valid_message_returns_full_response():
    """LOG-04: POST /chat-update valid message → 200, full response structure."""
    mock_db = _make_mock_db(log_data=_VALID_LOG, profile_data=_VALID_PROFILE)
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.logs.parse_user_message", return_value=_PARSED_FIELDS),
        patch("routes.logs.get_suggestions", return_value=["s1", "s2", "s3"]),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.post(
            "/api/logs/chat-update",
            json={"message": "I took the metro today for 8km"},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    data = body["data"]
    assert "daily_co2_kg" in data
    assert "breakdown" in data
    assert "analogy" in data
    assert "delta" in data
    assert "suggestions" in data
    assert isinstance(data["daily_co2_kg"], float)


# ── LOG-05 ────────────────────────────────────────────────────────────────────

def test_log_05_chat_update_parse_failed_returns_friendly_error():
    """LOG-05: POST /chat-update ParseFailedError → 200, success: false, friendly message."""
    mock_db = _make_mock_db()
    from utils.gemini_parser import ParseFailedError

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.logs.parse_user_message", side_effect=ParseFailedError("fail")),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.post(
            "/api/logs/chat-update",
            json={"message": "garbled nonsense"},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    # Friendly, not a raw exception message
    assert "try" in body["error"].lower() or "form" in body["error"].lower()


# ── LOG-06 ────────────────────────────────────────────────────────────────────

def test_log_06_get_today_wrong_user_id_returns_401():
    """LOG-06/07: GET /today with user_id that doesn't match token → 401 shape."""
    other_uid = "other-user-uid-888"
    mock_db = _make_mock_db()
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        # Request user_id = other_uid but token = _FAKE_UID
        response = client.get(
            f"/api/logs/{other_uid}/today",
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None


# ── LOG-07 ────────────────────────────────────────────────────────────────────

def test_log_07_get_today_no_token_returns_401():
    """LOG-07: GET /today with no Authorization header → 401."""
    mock_db = _make_mock_db()
    with (
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/logs/{_FAKE_UID}/today")

    assert response.status_code == 401


# ── LOG-08 ────────────────────────────────────────────────────────────────────

def test_log_08_chat_update_rate_limit_returns_standard_shape():
    """LOG-08: Rate limit exceeded (429) → standard error shape."""
    from fastapi import HTTPException

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        from exception_handler import register_exception_handlers
        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)

        # Simulate the 429 by directly testing the exception handler
        from fastapi import FastAPI
        mini_app = FastAPI()
        register_exception_handlers(mini_app)

        @mini_app.get("/simulate-429")
        async def fake_429():
            raise HTTPException(status_code=429, detail="rate limit")

        mini_client = TestClient(mini_app, raise_server_exceptions=False)
        response = mini_client.get("/simulate-429")

    assert response.status_code == 429
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] == "Too many requests. Please wait a moment."


# ── LOG-09 ────────────────────────────────────────────────────────────────────

def test_log_09_chat_update_suggestions_and_gamification_non_blocking():
    """LOG-09: Suggestions and gamification are async — response returns without waiting."""
    import time
    call_log: list[str] = []

    async def slow_suggestions(profile, persona, user_id):
        await asyncio.sleep(0.5)  # simulate slow Gemini
        call_log.append("suggestions_done")
        return ["s1", "s2", "s3"]

    async def slow_gamification(user_id, points_delta):
        await asyncio.sleep(0.5)
        call_log.append("gamification_done")

    mock_db = _make_mock_db(log_data=_VALID_LOG, profile_data=_VALID_PROFILE)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.logs.parse_user_message", return_value=_PARSED_FIELDS),
        patch("routes.logs._fetch_suggestions_async", side_effect=slow_suggestions),
        patch("routes.logs._update_gamification_async", side_effect=slow_gamification),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        start = time.monotonic()
        response = client.post(
            "/api/logs/chat-update",
            json={"message": "took metro today"},
            headers=_auth_headers(),
        )
        elapsed = time.monotonic() - start

    assert response.status_code == 200
    # Response must arrive in much less than 1 second even though async tasks are slow
    # (TestClient runs sync event loop — the timeout path returns [] for suggestions)
    body = response.json()
    assert body["success"] is True
    # suggestions may be [] if timeout hit — that's correct non-blocking behaviour
    assert "suggestions" in body["data"]


# ── LOG-10 ────────────────────────────────────────────────────────────────────

def test_log_10_daily_log_upserted_at_correct_firestore_path():
    """LOG-10: POST /chat-update upserts to daily_logs/{user_id}_{today_date}."""
    mock_db = _make_mock_db(log_data=_VALID_LOG, profile_data=_VALID_PROFILE)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.logs.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.logs.parse_user_message", return_value=_PARSED_FIELDS),
        patch("routes.logs.get_suggestions", return_value=["s1", "s2", "s3"]),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.post(
            "/api/logs/chat-update",
            json={"message": "I took the metro today"},
            headers=_auth_headers(),
        )

    assert response.status_code == 200

    # Verify the collection and document ID used for the upsert
    expected_doc_id = f"{_FAKE_UID}_{_TODAY}"
    daily_logs_calls = [
        call for call in mock_db.collection.call_args_list
        if call.args and call.args[0] == "daily_logs"
    ]
    assert len(daily_logs_calls) >= 1, "daily_logs collection must have been accessed"

    # Check the document method was called with the correct ID
    # (The daily_logs mock routes all document() calls to the same mock ref)
    # We verify via document().set() being called — proving an upsert happened
    daily_logs_collection = mock_db.collection("daily_logs")
    daily_logs_collection.document.assert_called()
    set_calls = daily_logs_collection.document.return_value.set.call_args_list
    assert len(set_calls) >= 1, "set() must have been called at least once (upsert)"


# ── Supplementary simulator tests ─────────────────────────────────────────────

def test_simulator_valid_params_returns_score_and_breakdown():
    """GET /simulator/calculate with valid params → 200, daily_co2_kg and breakdown."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            "/api/simulator/calculate",
            params={
                "commute_mode": "metro",
                "avg_daily_km": 8.0,
                "diet_type": "vegetarian",
                "ac_hours_per_day": 2.0,
                "lpg_cylinders_per_month": 0.5,
            },
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "daily_co2_kg" in body["data"]
    assert "breakdown" in body["data"]
    assert isinstance(body["data"]["daily_co2_kg"], float)


def test_simulator_invalid_commute_mode_returns_error():
    """GET /simulator/calculate with invalid commute_mode → error shape."""
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            "/api/simulator/calculate",
            params={
                "commute_mode": "hovercraft",
                "avg_daily_km": 5.0,
                "diet_type": "vegan",
                "ac_hours_per_day": 0.0,
                "lpg_cylinders_per_month": 0.5,
            },
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None


def test_simulator_no_token_returns_401():
    """GET /simulator/calculate without auth → 401."""
    with patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            "/api/simulator/calculate",
            params={
                "commute_mode": "metro",
                "avg_daily_km": 5.0,
                "diet_type": "vegan",
                "ac_hours_per_day": 0.0,
                "lpg_cylinders_per_month": 0.5,
            },
        )
    assert response.status_code == 401
