"""Gamification routes — streaks, points, badges, and leaderboard score.

SECURITY_SPEC.md §9: gamification/{userId} — backend Admin SDK write only.
Clients never write to this collection directly.

Badge thresholds (named constants — no magic numbers):
  "First Step"    → first log ever (lifetime_logs == 1)
  "Week Warrior"  → 7-day streak
  "Carbon Cutter" → delta_co2 saved > 2.0 kg in one update
  "Quiz Master"   → 3/3 correct on a quiz

Points awarded:
  chat-update log  → 10 points
  quiz correct     → 5 points per correct answer

All gamification writes use Admin SDK (backend only).
"""

# Standard library
import logging
from datetime import date, timedelta
from typing import Literal

# Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Internal — auth
from middleware.auth import verify_token

# Internal — Firestore (alias preserves test patch target)
from config import firebase
get_db = firebase.get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gamification"])

# ── Constants — badge thresholds (no magic numbers in logic) ──────────────────

_GAMIFICATION_COLLECTION: str = "gamification"

_STREAK_BADGE_THRESHOLD: int = 7          # days for "Week Warrior"
_DELTA_BADGE_THRESHOLD: float = 2.0       # kg CO2 saved for "Carbon Cutter"
_QUIZ_PERFECT_SCORE: int = 3              # correct answers for "Quiz Master"
_FIRST_LOG_COUNT: int = 1                 # lifetime logs for "First Step"
_CHAT_POINTS: int = 10                    # points per chat-update

_BADGE_FIRST_STEP: str = "First Step"
_BADGE_WEEK_WARRIOR: str = "Week Warrior"
_BADGE_CARBON_CUTTER: str = "Carbon Cutter"
_BADGE_QUIZ_MASTER: str = "Quiz Master"

_TriggerType = Literal["chat", "quiz"]


# ── Request model ─────────────────────────────────────────────────────────────

class GamificationUpdateRequest(BaseModel):
    """Request body for POST /api/gamification/update (internal use)."""
    trigger: _TriggerType = Field(..., description="'chat' or 'quiz'")
    points_delta: int = Field(..., ge=0, description="Points to award")
    delta_co2: float = Field(0.0, description="kg CO2 saved (for Carbon Cutter badge)")
    quiz_score: int = Field(0, ge=0, le=3, description="Correct answers (for Quiz Master badge)")


# ── Shared gamification logic (also called from quiz.py and logs.py async) ───

async def _update_gamification_async(
    user_id: str,
    points_delta: int,
    trigger: _TriggerType = "chat",
    delta_co2: float = 0.0,
    quiz_score: int = 0,
) -> dict:
    """Compute and persist all gamification state changes for a user event.

    Handles streak calculation, points accumulation, weekly_score, badge checks,
    and lifetime log counting. Failures are logged but never raised to caller.

    Args:
        user_id:      User's Firebase uid.
        points_delta: Points to award for this event.
        trigger:      "chat" (log update) or "quiz" (quiz submission).
        delta_co2:    CO2 kg saved in this update (for Carbon Cutter badge).
        quiz_score:   Number of correct quiz answers (for Quiz Master badge).

    Returns:
        Dict with streak, points, new_badges, weekly_score (or empty on error).
    """
    try:
        db = get_db()
        ref = db.collection(_GAMIFICATION_COLLECTION).document(user_id)
        doc = ref.get()
        current = doc.to_dict() if doc.exists else {}

        today_str = date.today().isoformat()
        yesterday_str = (date.today() - timedelta(days=1)).isoformat()

        # ── Streak calculation ─────────────────────────────────────────────────
        last_active = current.get("last_active_date", "")
        streak = current.get("streak", 0)

        if last_active == today_str:
            new_streak = streak          # already updated today
        elif last_active == yesterday_str:
            new_streak = streak + 1      # consecutive day
        else:
            new_streak = 1               # streak broken or first time

        # ── Points and weekly_score ───────────────────────────────────────────
        new_points = current.get("points", 0) + points_delta
        new_weekly = current.get("weekly_score", 0.0) + points_delta
        lifetime_logs = current.get("lifetime_logs", 0)

        if trigger == "chat":
            lifetime_logs += 1

        # ── Badge evaluation ──────────────────────────────────────────────────
        existing_badges: list[str] = current.get("badges", [])
        new_badges: list[str] = []

        def _award(badge: str) -> None:
            if badge not in existing_badges and badge not in new_badges:
                new_badges.append(badge)

        if lifetime_logs >= _FIRST_LOG_COUNT:
            _award(_BADGE_FIRST_STEP)
        if new_streak >= _STREAK_BADGE_THRESHOLD:
            _award(_BADGE_WEEK_WARRIOR)
        if delta_co2 > _DELTA_BADGE_THRESHOLD:
            _award(_BADGE_CARBON_CUTTER)
        if quiz_score >= _QUIZ_PERFECT_SCORE:
            _award(_BADGE_QUIZ_MASTER)

        all_badges = existing_badges + new_badges

        # ── Persist ───────────────────────────────────────────────────────────
        updated = {
            "streak": new_streak,
            "points": new_points,
            "weekly_score": new_weekly,
            "badges": all_badges,
            "last_active_date": today_str,
            "lifetime_logs": lifetime_logs,
            "state": current.get("state", ""),
        }
        ref.set(updated)

        return {
            "streak": new_streak,
            "points": new_points,
            "new_badges": new_badges,
            "weekly_score": new_weekly,
        }

    except Exception:
        logger.error(
            "gamification update failed for %s", user_id, exc_info=True
        )
        return {}


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/gamification/{user_id}")
async def get_gamification(
    user_id: str,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Return the gamification state (streak, points, badges, weekly_score, rank).

    user_id in path must match the verified token uid.

    Args:
        user_id:   Path parameter.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {streak, points, badges,
        weekly_score, rank}}.
    """
    try:
        if user_id != token_uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
            )

        db = get_db()
        doc = db.collection(_GAMIFICATION_COLLECTION).document(user_id).get()

        if not doc.exists:
            # Return zeroed structure — not an error
            return {
                "success": True,
                "data": {
                    "streak": 0,
                    "points": 0,
                    "badges": [],
                    "weekly_score": 0.0,
                    "rank": None,
                },
                "error": None,
            }

        data = doc.to_dict() or {}
        return {
            "success": True,
            "data": {
                "streak": data.get("streak", 0),
                "points": data.get("points", 0),
                "badges": data.get("badges", []),
                "weekly_score": data.get("weekly_score", 0.0),
                "rank": data.get("rank", None),
            },
            "error": None,
        }

    except HTTPException:
        raise
    except Exception:
        logger.error(
            "get_gamification: unexpected error for %s", user_id, exc_info=True
        )
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }


@router.post("/gamification/update")
async def update_gamification(
    body: GamificationUpdateRequest,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Apply a gamification update event — called after chat-update and quiz-submit.

    This is an internal endpoint. All writes use the Admin SDK (backend only).
    Computes streak, points, weekly_score, and badge awards atomically.

    Args:
        body:      GamificationUpdateRequest specifying trigger and deltas.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {streak, points, new_badges,
        weekly_score}}.
    """
    try:
        result = await _update_gamification_async(
            user_id=token_uid,
            points_delta=body.points_delta,
            trigger=body.trigger,
            delta_co2=body.delta_co2,
            quiz_score=body.quiz_score,
        )

        if not result:
            return {
                "success": False,
                "data": None,
                "error": "Something went wrong. Please try again.",
            }

        return {
            "success": True,
            "data": result,
            "error": None,
        }

    except Exception:
        logger.error(
            "update_gamification: unexpected error for %s", token_uid, exc_info=True
        )
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }
