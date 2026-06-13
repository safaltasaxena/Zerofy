"""Daily log routes — today's log, weekly trend, and NLP chat-update.

All business logic is in utils/. Routes are thin wrappers:
  validate → call utils → read/write Firestore → return response.

Firestore collections:
  daily_logs/{user_id}_{YYYY-MM-DD}   — upsert on chat-update, read for today/weekly
  profiles/{user_id}                  — read to get persona for suggestions
  gamification/{user_id}              — updated asynchronously after chat-update

Async background tasks (suggestions, gamification) are fired with
asyncio.create_task() — they do NOT block the response.
"""

# Standard library
import asyncio
import logging
from datetime import date, timedelta

# Third-party
from fastapi import APIRouter, Depends, HTTPException, status

# Internal — shared rate limiter (defined in main.py to avoid duplicate instances)
from main import limiter

# Internal — auth
from middleware.auth import verify_token

# Internal — Firestore (alias pattern preserves test patch target)
from config import firebase
get_db = firebase.get_db

# Internal — request models
from models.requests import ChatUpdateRequest

# Internal — utils
from utils.calculator import (
    CalculationError,
    calculate_breakdown,
    calculate_daily_score,
    calculate_delta,
)
from utils.analogy_engine import get_analogy
from utils.gemini_parser import ParseFailedError, parse_user_message
from utils.suggestion_engine import get_suggestions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["logs"])

# ── Constants ─────────────────────────────────────────────────────────────────

_DAILY_LOGS_COLLECTION: str = "daily_logs"
_PROFILES_COLLECTION: str = "profiles"
_GAMIFICATION_COLLECTION: str = "gamification"
_WEEKLY_TREND_LIMIT: int = 7
_CHAT_RATE_LIMIT: str = "10/minute"

_ZEROED_LOG: dict = {
    "commute_mode": None,
    "avg_daily_km": 0.0,
    "diet_type": None,
    "ac_hours_per_day": 0.0,
    "lpg_cylinders_per_month": 0.0,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _today_doc_id(user_id: str) -> str:
    """Build the Firestore document ID for today's log.

    Args:
        user_id: Verified uid from Firebase token.

    Returns:
        String of the form "{user_id}_{YYYY-MM-DD}".
    """
    return f"{user_id}_{date.today().isoformat()}"


def _seven_days_ago() -> str:
    """Return the ISO date string for exactly 7 days ago.

    Returns:
        String of the form "YYYY-MM-DD".
    """
    return (date.today() - timedelta(days=_WEEKLY_TREND_LIMIT)).isoformat()


def _assert_owner(user_id: str, token_uid: str) -> bool:
    """Return True if the token uid matches the requested user_id.

    Args:
        user_id:   user_id from the URL path parameter.
        token_uid: uid extracted from the verified Firebase token.

    Returns:
        True if they match, False otherwise.
    """
    return user_id == token_uid


def _zeroed_response(user_id: str) -> dict:
    """Build the zeroed structure returned when no log exists for today.

    Args:
        user_id: The requesting user's uid.

    Returns:
        Standard zeroed daily data dict.
    """
    return {
        "log": _ZEROED_LOG,
        "daily_co2_kg": 0.0,
        "breakdown": {
            "transport": 0.0,
            "diet": 0.0,
            "electricity": 0.0,
            "lpg": 0.0,
            "total": 0.0,
        },
        "analogy": get_analogy(0.0),
    }


async def _update_gamification_async(user_id: str, points_delta: int) -> None:
    """Update gamification document asynchronously — does not block response.

    Reads the existing gamification doc, increments points and updates streak.
    Failures are logged but never surfaced to the caller.

    Args:
        user_id:      The user's uid.
        points_delta: Points earned from this chat update.
    """
    try:
        db = get_db()
        ref = db.collection(_GAMIFICATION_COLLECTION).document(user_id)
        doc = ref.get()
        current = doc.to_dict() if doc.exists else {}
        today_str = date.today().isoformat()
        last_active = current.get("last_active_date", "")
        streak = current.get("streak", 0)

        if last_active == today_str:
            # Already updated today — only increment points
            new_streak = streak
        elif last_active == (date.today() - timedelta(days=1)).isoformat():
            new_streak = streak + 1
        else:
            new_streak = 1

        ref.set({
            "points": current.get("points", 0) + points_delta,
            "streak": new_streak,
            "last_active_date": today_str,
            "weekly_score": current.get("weekly_score", 0.0),
            "state": current.get("state", ""),
        }, merge=True)
    except Exception:
        logger.error(
            "gamification update failed for %s", user_id, exc_info=True
        )


async def _fetch_suggestions_async(
    profile: dict, persona: str, user_id: str
) -> list[str]:
    """Fetch polished suggestions asynchronously.

    Returns rule-based suggestions if Gemini polish fails — never raises.

    Args:
        profile:  Current user profile dict.
        persona:  User persona string.
        user_id:  For logging only.

    Returns:
        List of 3 suggestion strings.
    """
    try:
        return get_suggestions(profile, persona)
    except Exception:
        logger.warning(
            "suggestions fetch failed for %s", user_id, exc_info=True
        )
        return []


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/logs/{user_id}/today")
async def get_today_log(
    user_id: str,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Return today's carbon log for the authenticated user.

    If no log exists yet today, returns a zeroed structure — not an error.
    user_id in the path must match the token uid.

    Args:
        user_id:   Path parameter — the user whose log is requested.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {log, daily_co2_kg, breakdown, analogy}}.
    """
    try:
        if not _assert_owner(user_id, token_uid):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
            )

        db = get_db()
        doc_id = _today_doc_id(user_id)
        doc = db.collection(_DAILY_LOGS_COLLECTION).document(doc_id).get()

        if not doc.exists:
            return {
                "success": True,
                "data": _zeroed_response(user_id),
                "error": None,
            }

        log = doc.to_dict() or {}
        daily_co2_kg = calculate_daily_score(log)
        breakdown = calculate_breakdown(log)
        analogy = get_analogy(daily_co2_kg)

        return {
            "success": True,
            "data": {
                "log": log,
                "daily_co2_kg": daily_co2_kg,
                "breakdown": breakdown,
                "analogy": analogy,
            },
            "error": None,
        }

    except Exception:
        logger.error(
            "get_today_log: unexpected error for %s", user_id, exc_info=True
        )
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }


@router.get("/logs/{user_id}/weekly")
async def get_weekly_trend(
    user_id: str,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Return the last 7 days of CO2 scores for trend chart display.

    Queries daily_logs with user_id filter and date >= 7 days ago.
    Requires the composite index on user_id + date (firestore.indexes.json).

    Args:
        user_id:   Path parameter — the user whose trend is requested.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {trend: [{date, daily_co2_kg}]}}.
    """
    try:
        if not _assert_owner(user_id, token_uid):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
            )

        db = get_db()
        seven_ago = _seven_days_ago()

        docs = (
            db.collection(_DAILY_LOGS_COLLECTION)
            .where("user_id", "==", user_id)
            .where("date", ">=", seven_ago)
            .order_by("date")
            .limit(_WEEKLY_TREND_LIMIT)
            .stream()
        )

        trend = []
        for doc in docs:
            entry = doc.to_dict() or {}
            try:
                daily_co2_kg = calculate_daily_score(entry)
                trend.append({
                    "date": entry.get("date", ""),
                    "daily_co2_kg": daily_co2_kg,
                })
            except CalculationError:
                # Skip malformed log entries — never fail the whole query
                continue

        return {
            "success": True,
            "data": {"trend": trend},
            "error": None,
        }

    except Exception:
        logger.error(
            "get_weekly_trend: unexpected error for %s", user_id, exc_info=True
        )
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }


@router.post("/logs/chat-update")
@limiter.limit(_CHAT_RATE_LIMIT)
async def chat_update(
    request,   # injected by slowapi — must be first positional after self
    body: ChatUpdateRequest,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Parse a natural language habit update and apply it to today's log.

    Pipeline (per EFFICIENCY.md §2):
      1. parse_user_message()  — 1 Gemini call + 1 retry max
      2. Upsert daily_logs/{user_id}_{today}
      3. calculate_daily_score()
      4. calculate_breakdown()
      5. calculate_delta()
      6. get_analogy()
      7. get_suggestions() — fired async, does not block response
      8. update gamification — fired async, does not block response

    Args:
        request:   Starlette Request — required by slowapi rate limiter.
        body:      Validated ChatUpdateRequest.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {daily_co2_kg, breakdown, analogy,
        delta, suggestions}}.
    """
    user_id = token_uid  # user_id always from token — never from body

    try:
        # Step 1 — parse user message via Gemini
        parsed_fields = parse_user_message(body.message)

        db = get_db()
        doc_id = _today_doc_id(user_id)

        # Load existing log to merge into (or start fresh)
        existing_doc = db.collection(_DAILY_LOGS_COLLECTION).document(doc_id).get()
        existing_log = existing_doc.to_dict() if existing_doc.exists else {}
        old_score = 0.0
        if existing_log:
            try:
                old_score = calculate_daily_score(existing_log)
            except CalculationError:
                old_score = 0.0

        # Step 2 — merge parsed fields into existing log, upsert
        updated_log = {**existing_log}
        for key, val in parsed_fields.items():
            if val is not None:
                updated_log[key] = val
        updated_log["user_id"] = user_id
        updated_log["date"] = date.today().isoformat()

        db.collection(_DAILY_LOGS_COLLECTION).document(doc_id).set(updated_log)

        # Step 3-6 — calculations (pure math — no Gemini)
        new_score = calculate_daily_score(updated_log)
        breakdown = calculate_breakdown(updated_log)
        delta = calculate_delta(old_score, new_score)
        analogy = get_analogy(new_score)

        # Load profile for persona-aware suggestions
        profile_doc = db.collection(_PROFILES_COLLECTION).document(user_id).get()
        profile = profile_doc.to_dict() if profile_doc.exists else {}
        persona = profile.get("persona", "general")

        # Step 7 — suggestions: run in background, don't await
        suggestions_task = asyncio.create_task(
            _fetch_suggestions_async(updated_log, persona, user_id)
        )

        # Step 8 — gamification: run in background, don't await
        asyncio.create_task(_update_gamification_async(user_id, points_delta=10))

        # Await suggestions with a short timeout so they can be included in response
        # if ready quickly; otherwise return empty list — frontend handles gracefully
        try:
            suggestions = await asyncio.wait_for(suggestions_task, timeout=3.0)
        except asyncio.TimeoutError:
            suggestions = []

        return {
            "success": True,
            "data": {
                "daily_co2_kg": new_score,
                "breakdown": breakdown,
                "analogy": analogy,
                "delta": delta,
                "suggestions": suggestions,
            },
            "error": None,
        }

    except ParseFailedError as e:
        logger.warning("chat_update: parse failed for %s: %s", user_id, e)
        return {
            "success": False,
            "data": None,
            "error": "Couldn't understand that — please try the quick-update form below.",
        }
    except CalculationError as e:
        logger.warning("chat_update: calculation error for %s: %s", user_id, e)
        return {
            "success": False,
            "data": None,
            "error": "Could not calculate your updated score. Please try again.",
        }
    except Exception:
        logger.error("chat_update: unexpected error for %s", user_id, exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }
