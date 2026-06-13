"""Tests for routes/quiz.py and routes/gamification.py.

Maps to QUIZ-01 through QUIZ-12.

Mocking strategy:
  - firebase_admin.auth.verify_id_token → fake decoded token.
  - routes.quiz.get_db / routes.gamification.get_db → mock Firestore clients.
  - google.generativeai (genai) → mock model to avoid real Gemini calls.
  No real Firebase, Firestore, or Gemini calls in any test.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("RATE_LIMIT_STORAGE_URI", "memory://")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Shared constants ──────────────────────────────────────────────────────────

_FAKE_UID = "quiz-user-uid-777"
_FAKE_TOKEN = "quiz.bearer.token"
_TODAY = date.today().isoformat()
_DOC_ID = f"{_FAKE_UID}_{_TODAY}"

_FAKE_QUESTIONS = [
    {
        "question": "What is the most effective way to reduce transport emissions?",
        "options": ["Drive alone", "Take metro", "Use AC car", "Fly"],
        "correct_index": 1,
        "explanation": "Metro produces 95% less CO2 per km than private cars.",
    },
    {
        "question": "Which diet has the lowest carbon footprint?",
        "options": ["Non-veg", "Eggetarian", "Vegetarian", "Vegan"],
        "correct_index": 3,
        "explanation": "Vegan diet avoids animal products entirely.",
    },
    {
        "question": "What AC temperature saves the most energy?",
        "options": ["18°C", "20°C", "24°C", "28°C"],
        "correct_index": 2,
        "explanation": "24°C is optimal — balances comfort and energy savings.",
    },
]

_CACHED_QUIZ_DOC = {
    "user_id": _FAKE_UID,
    "date": _TODAY,
    "questions": _FAKE_QUESTIONS,
    "submitted": False,
    "score": None,
}

_GAMIFICATION_DATA = {
    "streak": 3,
    "points": 50,
    "badges": ["First Step"],
    "weekly_score": 50.0,
    "last_active_date": _TODAY,
    "lifetime_logs": 5,
    "state": "Maharashtra",
}


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _mock_doc(data: dict | None) -> MagicMock:
    doc = MagicMock()
    doc.exists = data is not None
    doc.to_dict.return_value = data
    return doc


def _make_gemini_mock(response_text: str) -> MagicMock:
    """Return a mock genai module whose GenerativeModel().generate_content() returns response_text."""
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    return mock_genai


def _make_quiz_db(
    quiz_data: dict | None = None,
    log_data: dict | None = None,
    gamification_data: dict | None = None,
) -> MagicMock:
    """Build a multi-collection mock Firestore client for quiz routes."""
    db = MagicMock()

    def _collection(name: str):
        coll = MagicMock()
        if name == "quiz_results":
            doc_ref = MagicMock()
            doc_ref.get.return_value = _mock_doc(quiz_data)
            doc_ref.set.return_value = None
            coll.document.return_value = doc_ref
        elif name == "daily_logs":
            doc_ref = MagicMock()
            doc_ref.get.return_value = _mock_doc(log_data)
            coll.document.return_value = doc_ref
        elif name == "gamification":
            doc_ref = MagicMock()
            doc_ref.get.return_value = _mock_doc(gamification_data)
            doc_ref.set.return_value = None
            coll.document.return_value = doc_ref
        return coll

    db.collection.side_effect = _collection
    return db


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_FAKE_TOKEN}"}


@pytest.fixture(scope="function")
def client():
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("config.firebase.get_db", return_value=_make_quiz_db()),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        yield TestClient(create_app(), raise_server_exceptions=False)


# ── QUIZ-01 ───────────────────────────────────────────────────────────────────

def test_quiz_01_cached_quiz_returned_without_gemini_call():
    """QUIZ-01: GET /today — cached quiz exists → Gemini NOT called, generated_fresh: false."""
    mock_db = _make_quiz_db(quiz_data=_CACHED_QUIZ_DOC)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.quiz.genai") as mock_genai,
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/quiz/today/{_FAKE_UID}", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["generated_fresh"] is False
    assert len(body["data"]["questions"]) == 3
    # Gemini must NOT have been called
    mock_genai.GenerativeModel.assert_not_called()


# ── QUIZ-02 ───────────────────────────────────────────────────────────────────

def test_quiz_02_no_cache_calls_gemini_once_and_caches():
    """QUIZ-02: GET /today — no cache → Gemini called once, result cached, generated_fresh: true."""
    mock_db = _make_quiz_db(quiz_data=None)
    gemini_response = json.dumps(_FAKE_QUESTIONS)
    mock_genai = _make_gemini_mock(gemini_response)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.quiz.genai", mock_genai),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/quiz/today/{_FAKE_UID}", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["generated_fresh"] is True
    assert len(body["data"]["questions"]) == 3
    # Gemini must have been called exactly once
    mock_genai.GenerativeModel.return_value.generate_content.assert_called_once()
    # Firestore set() must have been called to cache
    quiz_coll = mock_db.collection("quiz_results")
    quiz_coll.document.return_value.set.assert_called_once()


# ── QUIZ-03 ───────────────────────────────────────────────────────────────────

def test_quiz_03_gemini_failure_returns_friendly_error():
    """QUIZ-03: GET /today — Gemini fails → 200, success: false, friendly error."""
    mock_db = _make_quiz_db(quiz_data=None)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.quiz.genai") as mock_genai,
    ):
        mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("API down")
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/quiz/today/{_FAKE_UID}", headers=_auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    # Friendly — must not expose internal error details
    assert "RuntimeError" not in body["error"]
    assert "API" not in body["error"]
    assert "try again" in body["error"].lower() or "later" in body["error"].lower()


# ── QUIZ-04 ───────────────────────────────────────────────────────────────────

def test_quiz_04_submit_valid_answers_returns_score_and_points():
    """QUIZ-04: POST /submit valid answers → 200, score and points_earned."""
    mock_db = _make_quiz_db(quiz_data=_CACHED_QUIZ_DOC)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.gamification._update_gamification_async", return_value={}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        # Correct answers for _FAKE_QUESTIONS: [1, 3, 2]
        response = client.post(
            "/api/quiz/submit",
            json={"answers": [1, 3, 2]},
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["score"] == 3
    assert body["data"]["points_earned"] == 15   # 3 × 5
    assert all(body["data"]["correct_answers"])


def test_quiz_04_partial_correct_answers():
    """QUIZ-04 (variant): partial correct answers → correct score and points."""
    mock_db = _make_quiz_db(quiz_data=_CACHED_QUIZ_DOC)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.gamification._update_gamification_async", return_value={}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        # Only first answer correct (1), rest wrong
        response = client.post(
            "/api/quiz/submit",
            json={"answers": [1, 0, 0]},
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["success"] is True
    assert body["data"]["score"] == 1
    assert body["data"]["points_earned"] == 5


# ── QUIZ-05 ───────────────────────────────────────────────────────────────────

def test_quiz_05_submit_no_token_returns_401(client):
    """QUIZ-05: POST /submit with no token → 401."""
    response = client.post("/api/quiz/submit", json={"answers": [0, 0, 0]})
    assert response.status_code == 401


def test_quiz_05_get_today_wrong_user_id_returns_401():
    """QUIZ-05 (GET): GET /today with mismatched user_id → auth failure shape."""
    other_uid = "other-uid-888"

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            f"/api/quiz/today/{other_uid}",
            headers=_auth_headers(),
        )

    assert response.status_code == 401


# ── QUIZ-06 ───────────────────────────────────────────────────────────────────

def test_quiz_06_get_gamification_valid_token_returns_state():
    """QUIZ-06: GET /gamification valid token → 200, returns streak, points, badges, weekly_score."""
    mock_db = _make_quiz_db(gamification_data=_GAMIFICATION_DATA)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.gamification.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            f"/api/gamification/{_FAKE_UID}",
            headers=_auth_headers(),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["streak"] == 3
    assert data["points"] == 50
    assert "First Step" in data["badges"]
    assert data["weekly_score"] == 50.0


def test_quiz_06_get_gamification_no_doc_returns_zeroed():
    """QUIZ-06 (no doc): GET /gamification with no existing doc → 200, zeroed structure."""
    mock_db = _make_quiz_db(gamification_data=None)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.gamification.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            f"/api/gamification/{_FAKE_UID}",
            headers=_auth_headers(),
        )

    body = response.json()
    assert body["success"] is True
    assert body["data"]["streak"] == 0
    assert body["data"]["points"] == 0
    assert body["data"]["badges"] == []


# ── QUIZ-07 ───────────────────────────────────────────────────────────────────

def test_quiz_07_chat_trigger_awards_10_points():
    """QUIZ-07: Gamification update with chat trigger awards 10 points."""
    import asyncio
    from routes.gamification import _update_gamification_async

    mock_db = _make_quiz_db(gamification_data={
        "streak": 1,
        "points": 0,
        "badges": [],
        "weekly_score": 0.0,
        "last_active_date": "",
        "lifetime_logs": 0,
        "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID,
                points_delta=10,
                trigger="chat",
                delta_co2=0.0,
                quiz_score=0,
            )
        )

    assert result["points"] == 10


# ── QUIZ-08 ───────────────────────────────────────────────────────────────────

def test_quiz_08_quiz_trigger_awards_5_points_per_correct():
    """QUIZ-08: Gamification update for quiz awards 5 points per correct answer."""
    import asyncio
    from routes.gamification import _update_gamification_async

    mock_db = _make_quiz_db(gamification_data={
        "streak": 0,
        "points": 0,
        "badges": [],
        "weekly_score": 0.0,
        "last_active_date": "",
        "lifetime_logs": 0,
        "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID,
                points_delta=15,   # 3 correct × 5 points
                trigger="quiz",
                delta_co2=0.0,
                quiz_score=3,
            )
        )

    assert result["points"] == 15


# ── QUIZ-09 ───────────────────────────────────────────────────────────────────

def test_quiz_09_7_day_streak_awards_week_warrior_badge():
    """QUIZ-09: 7-day streak → 'Week Warrior' badge awarded."""
    import asyncio
    from datetime import date, timedelta
    from routes.gamification import _update_gamification_async

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    mock_db = _make_quiz_db(gamification_data={
        "streak": 6,
        "points": 60,
        "badges": ["First Step"],
        "weekly_score": 60.0,
        "last_active_date": yesterday,
        "lifetime_logs": 6,
        "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID,
                points_delta=10,
                trigger="chat",
                delta_co2=0.0,
                quiz_score=0,
            )
        )

    assert result["streak"] == 7
    assert "Week Warrior" in result["new_badges"]


# ── QUIZ-10 ───────────────────────────────────────────────────────────────────

def test_quiz_10_delta_over_2kg_awards_carbon_cutter():
    """QUIZ-10: delta_co2 > 2.0 kg saved → 'Carbon Cutter' badge awarded."""
    import asyncio
    from routes.gamification import _update_gamification_async

    mock_db = _make_quiz_db(gamification_data={
        "streak": 1,
        "points": 10,
        "badges": ["First Step"],
        "weekly_score": 10.0,
        "last_active_date": "",
        "lifetime_logs": 1,
        "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID,
                points_delta=10,
                trigger="chat",
                delta_co2=2.5,   # > 2.0 threshold
                quiz_score=0,
            )
        )

    assert "Carbon Cutter" in result["new_badges"]


def test_quiz_10_delta_exactly_2kg_does_not_award_badge():
    """QUIZ-10 (boundary): delta_co2 == 2.0 → Carbon Cutter NOT awarded (> not >=)."""
    import asyncio
    from routes.gamification import _update_gamification_async

    mock_db = _make_quiz_db(gamification_data={
        "streak": 0, "points": 0, "badges": [], "weekly_score": 0.0,
        "last_active_date": "", "lifetime_logs": 0, "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID, points_delta=10, trigger="chat",
                delta_co2=2.0, quiz_score=0,
            )
        )

    assert "Carbon Cutter" not in result["new_badges"]


# ── QUIZ-11 ───────────────────────────────────────────────────────────────────

def test_quiz_11_quiz_cached_at_correct_firestore_path():
    """QUIZ-11: On cache miss, quiz cached at quiz_results/{user_id}_{date}."""
    mock_db = _make_quiz_db(quiz_data=None)
    gemini_response = json.dumps(_FAKE_QUESTIONS)
    mock_genai = _make_gemini_mock(gemini_response)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.quiz.genai", mock_genai),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(f"/api/quiz/today/{_FAKE_UID}", headers=_auth_headers())

    assert response.status_code == 200
    # Verify collection was called with "quiz_results"
    quiz_calls = [
        c for c in mock_db.collection.call_args_list
        if c.args and c.args[0] == "quiz_results"
    ]
    assert len(quiz_calls) >= 1

    # Verify set() was called — meaning the doc was cached
    quiz_doc_ref = mock_db.collection("quiz_results").document.return_value
    quiz_doc_ref.set.assert_called_once()

    # Verify the document ID used
    expected_doc_id = f"{_FAKE_UID}_{_TODAY}"
    mock_db.collection("quiz_results").document.assert_called_with(expected_doc_id)


# ── QUIZ-12 ───────────────────────────────────────────────────────────────────

def test_quiz_12_gemini_called_0_times_on_cached_hit():
    """QUIZ-12: Second request for same day's quiz → Gemini called 0 times."""
    # Simulate a cached quiz already in Firestore
    mock_db = _make_quiz_db(quiz_data=_CACHED_QUIZ_DOC)

    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("routes.quiz.get_db", return_value=mock_db),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
        patch("routes.quiz.genai") as mock_genai,
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)

        # First request (cache hit on first try — simulates "second call same day")
        r1 = client.get(f"/api/quiz/today/{_FAKE_UID}", headers=_auth_headers())
        # Second request
        r2 = client.get(f"/api/quiz/today/{_FAKE_UID}", headers=_auth_headers())

    assert r1.status_code == 200
    assert r2.status_code == 200
    # Gemini must never have been called in either request
    mock_genai.GenerativeModel.assert_not_called()
    assert r1.json()["data"]["generated_fresh"] is False
    assert r2.json()["data"]["generated_fresh"] is False


# ── Additional gamification tests ─────────────────────────────────────────────

def test_first_step_badge_on_first_log():
    """'First Step' badge awarded when lifetime_logs reaches 1."""
    import asyncio
    from routes.gamification import _update_gamification_async

    # No existing document — first ever log
    mock_db = _make_quiz_db(gamification_data=None)

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID, points_delta=10, trigger="chat",
                delta_co2=0.0, quiz_score=0,
            )
        )

    assert "First Step" in result["new_badges"]


def test_quiz_master_badge_on_perfect_quiz():
    """'Quiz Master' badge awarded on 3/3 correct quiz answers."""
    import asyncio
    from routes.gamification import _update_gamification_async

    mock_db = _make_quiz_db(gamification_data={
        "streak": 0, "points": 0, "badges": [], "weekly_score": 0.0,
        "last_active_date": "", "lifetime_logs": 0, "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID, points_delta=15, trigger="quiz",
                delta_co2=0.0, quiz_score=3,
            )
        )

    assert "Quiz Master" in result["new_badges"]


def test_badge_not_duplicated_if_already_earned():
    """A badge is not added twice if the user already has it."""
    import asyncio
    from routes.gamification import _update_gamification_async

    # User already has Week Warrior
    mock_db = _make_quiz_db(gamification_data={
        "streak": 7, "points": 100, "badges": ["First Step", "Week Warrior"],
        "weekly_score": 100.0, "last_active_date": "",
        "lifetime_logs": 7, "state": "",
    })

    with patch("routes.gamification.get_db", return_value=mock_db):
        result = asyncio.get_event_loop().run_until_complete(
            _update_gamification_async(
                user_id=_FAKE_UID, points_delta=10, trigger="chat",
                delta_co2=0.0, quiz_score=0,
            )
        )

    # Week Warrior must NOT appear in new_badges again
    assert "Week Warrior" not in result["new_badges"]


def test_get_gamification_wrong_user_returns_401():
    """GET /gamification/{other_uid} when token is for different user → 401."""
    other_uid = "other-gamification-uid"
    with (
        patch("firebase_admin.auth.verify_id_token", return_value={"uid": _FAKE_UID}),
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get(
            f"/api/gamification/{other_uid}",
            headers=_auth_headers(),
        )
    assert response.status_code == 401
