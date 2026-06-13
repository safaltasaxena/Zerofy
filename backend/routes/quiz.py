"""Quiz routes — generate personalised daily quiz questions and score user answers.

EFFICIENCY.md §2: Quiz generation = 1 Gemini call per user per day.
Results are cached in Firestore at quiz_results/{user_id}_{date}.
On subsequent loads for the same day, Firestore is served directly — 0 Gemini calls.

Gemini call budget per user action:
  GET /api/quiz/today — first load today: 1 Gemini call + cache
  GET /api/quiz/today — subsequent loads: 0 Gemini calls (Firestore cache)
  POST /api/quiz/submit — 0 Gemini calls (pure math)
"""

# Standard library
import json
import logging
import os
import re
from datetime import date

# Third-party
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

# Internal — shared rate limiter
from main import limiter

# Internal — auth
from middleware.auth import verify_token

# Internal — Firestore (alias preserves test patch target)
from config import firebase
get_db = firebase.get_db

# Internal — calculator for today's breakdown
from utils.calculator import CalculationError, calculate_breakdown

logger = logging.getLogger(__name__)

router = APIRouter(tags=["quiz"])

# ── Constants ─────────────────────────────────────────────────────────────────

_QUIZ_RESULTS_COLLECTION: str = "quiz_results"
_DAILY_LOGS_COLLECTION: str = "daily_logs"
_GAMIFICATION_COLLECTION: str = "gamification"
_QUIZ_QUESTION_COUNT: int = 3
_GEMINI_MODEL: str = "gemini-1.5-flash"
_QUIZ_RATE_LIMIT: str = "30/minute"
_POINTS_PER_CORRECT: int = 5


# ── Request models ────────────────────────────────────────────────────────────

class QuizSubmitRequest(BaseModel):
    """Request body for POST /api/quiz/submit."""
    answers: list[int] = Field(
        ...,
        min_length=_QUIZ_QUESTION_COUNT,
        max_length=_QUIZ_QUESTION_COUNT,
        description="Exactly 3 answer indices (one per question)",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _today_doc_id(user_id: str) -> str:
    """Build the Firestore document ID for today's quiz result.

    Args:
        user_id: Verified uid from Firebase token.

    Returns:
        String of the form "{user_id}_{YYYY-MM-DD}".
    """
    return f"{user_id}_{date.today().isoformat()}"


def _assert_owner(user_id: str, token_uid: str) -> bool:
    """Return True if the token uid matches the path user_id.

    Args:
        user_id:   user_id from URL path parameter.
        token_uid: uid from verified Firebase token.

    Returns:
        True if they match.
    """
    return user_id == token_uid


def _worst_category(breakdown: dict) -> str:
    """Return the habit category with the highest CO2 contribution.

    Args:
        breakdown: Dict with keys transport, diet, electricity, lpg.

    Returns:
        Category name string, or "diet" as default.
    """
    try:
        categories = {k: v for k, v in breakdown.items() if k != "total"}
        if not categories:
            return "diet"
        return max(categories, key=lambda k: categories[k])
    except Exception:
        return "diet"


def _build_quiz_prompt(worst_category: str) -> str:
    """Build the Gemini prompt for quiz generation.

    Args:
        worst_category: The user's highest-emission habit category.

    Returns:
        Prompt string — no user-generated content injected.
    """
    return (
        f"Generate exactly {_QUIZ_QUESTION_COUNT} multiple-choice quiz questions about "
        f"reducing carbon emissions, focused on the category: {worst_category}. "
        f"Personalise for Indian users and Indian context. "
        f"Return ONLY a valid JSON array — no markdown, no explanation, no code fences. "
        f"Each element must have exactly these fields: "
        f'question (string), options (array of exactly 4 strings), '
        f'correct_index (integer 0-3), explanation (string under 30 words). '
        f"Example format: "
        f'[{{"question":"...","options":["a","b","c","d"],"correct_index":0,"explanation":"..."}}]'
    )


def _parse_quiz_response(raw: str) -> list[dict]:
    """Parse and validate Gemini's quiz JSON response.

    Strips markdown fences if present, then json.loads, then validates schema.

    Args:
        raw: Raw text from Gemini API.

    Returns:
        List of exactly 3 validated question dicts.

    Raises:
        ValueError: If the response cannot be parsed or fails schema validation.
    """
    try:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        questions = json.loads(cleaned)

        if not isinstance(questions, list) or len(questions) != _QUIZ_QUESTION_COUNT:
            raise ValueError(
                f"Expected list of {_QUIZ_QUESTION_COUNT} questions, got {type(questions)}"
            )
        for q in questions:
            if not isinstance(q.get("question"), str):
                raise ValueError("Missing or invalid 'question' field")
            opts = q.get("options", [])
            if not isinstance(opts, list) or len(opts) != 4:
                raise ValueError("'options' must be a list of exactly 4 strings")
            if not isinstance(q.get("correct_index"), int):
                raise ValueError("'correct_index' must be an int")
            if not isinstance(q.get("explanation"), str):
                raise ValueError("Missing or invalid 'explanation' field")
        return questions
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Quiz parse error: {e}") from e


def _call_gemini_for_quiz(worst_category: str) -> list[dict]:
    """Generate quiz questions via a single Gemini API call.

    Args:
        worst_category: Category to personalise questions around.

    Returns:
        List of 3 validated question dicts.

    Raises:
        ValueError: If the API call fails or the response is unparsable.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_GEMINI_MODEL)
        prompt = _build_quiz_prompt(worst_category)
        response = model.generate_content(prompt)
        return _parse_quiz_response(response.text)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Gemini API call failed: {e}") from e


def _score_answers(questions: list[dict], answers: list[int]) -> dict:
    """Calculate the quiz score from submitted answers.

    Args:
        questions: List of question dicts (must include correct_index).
        answers:   List of submitted answer indices (one per question).

    Returns:
        Dict with score (int), correct_answers (list[bool]), points_earned (int).

    Raises:
        ValueError: If answer list length does not match question count.
    """
    try:
        if len(answers) != len(questions):
            raise ValueError(
                f"Expected {len(questions)} answers, got {len(answers)}"
            )
        correct_answers = [
            answers[i] == q["correct_index"]
            for i, q in enumerate(questions)
        ]
        score = sum(correct_answers)
        points_earned = score * _POINTS_PER_CORRECT
        return {
            "score": score,
            "correct_answers": correct_answers,
            "points_earned": points_earned,
        }
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Score calculation failed: {e}") from e


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/quiz/today/{user_id}")
@limiter.limit(_QUIZ_RATE_LIMIT)
async def get_today_quiz(
    request: Request,
    user_id: str,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Return today's personalised quiz — from Firestore cache or freshly generated.

    Checks Firestore first (0 Gemini calls if cached). On cache miss, calls Gemini
    once, caches the result, and returns generated_fresh: true.
    Questions are personalised to the user's worst-emission habit category.

    Args:
        request:   Starlette Request — required by slowapi.
        user_id:   Path parameter.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {questions, generated_fresh}}.
    """
    try:
        if not _assert_owner(user_id, token_uid):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed.",
            )

        db = get_db()
        doc_id = _today_doc_id(user_id)

        # Cache hit — return without calling Gemini
        cached_doc = db.collection(_QUIZ_RESULTS_COLLECTION).document(doc_id).get()
        if cached_doc.exists:
            cached = cached_doc.to_dict() or {}
            questions = cached.get("questions", [])
            if questions:
                return {
                    "success": True,
                    "data": {"questions": questions, "generated_fresh": False},
                    "error": None,
                }

        # Determine worst habit category from today's log breakdown
        today_log_id = f"{user_id}_{date.today().isoformat()}"
        log_doc = db.collection(_DAILY_LOGS_COLLECTION).document(today_log_id).get()
        log_data = log_doc.to_dict() if log_doc.exists else {}

        worst_category = "diet"  # fallback
        if log_data:
            try:
                breakdown = calculate_breakdown(log_data)
                worst_category = _worst_category(breakdown)
            except CalculationError:
                worst_category = "diet"

        # Cache miss — call Gemini once
        questions = _call_gemini_for_quiz(worst_category)

        # Cache result in Firestore
        db.collection(_QUIZ_RESULTS_COLLECTION).document(doc_id).set({
            "user_id": user_id,
            "date": date.today().isoformat(),
            "questions": questions,
            "submitted": False,
            "score": None,
        })

        return {
            "success": True,
            "data": {"questions": questions, "generated_fresh": True},
            "error": None,
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("get_today_quiz: generation failed for %s: %s", user_id, e)
        return {
            "success": False,
            "data": None,
            "error": "Couldn't generate your quiz right now. Please try again later.",
        }
    except Exception:
        logger.error("get_today_quiz: unexpected error for %s", user_id, exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }


@router.post("/quiz/submit")
async def submit_quiz(
    body: QuizSubmitRequest,
    token_uid: str = Depends(verify_token),
) -> dict:
    """Score submitted quiz answers and persist the result to Firestore.

    Triggers a gamification update asynchronously (non-blocking).

    Args:
        body:      List of 3 integer answer indices.
        token_uid: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {score, correct_answers, points_earned}}.
    """
    import asyncio
    user_id = token_uid

    try:
        db = get_db()
        doc_id = _today_doc_id(user_id)

        quiz_doc = db.collection(_QUIZ_RESULTS_COLLECTION).document(doc_id).get()
        if not quiz_doc.exists:
            return {
                "success": False,
                "data": None,
                "error": "No quiz found for today. Please load the quiz first.",
            }

        quiz_data = quiz_doc.to_dict() or {}
        questions = quiz_data.get("questions", [])
        if not questions:
            return {
                "success": False,
                "data": None,
                "error": "Quiz data is incomplete. Please reload your quiz.",
            }

        result = _score_answers(questions, body.answers)

        # Persist score to Firestore
        db.collection(_QUIZ_RESULTS_COLLECTION).document(doc_id).set({
            **quiz_data,
            "submitted": True,
            "answers": body.answers,
            "score": result["score"],
            "points_earned": result["points_earned"],
        })

        # Trigger gamification async — non-blocking
        from routes.gamification import _update_gamification_async
        asyncio.create_task(
            _update_gamification_async(
                user_id=user_id,
                points_delta=result["points_earned"],
                trigger="quiz",
                delta_co2=0.0,
                quiz_score=result["score"],
            )
        )

        return {
            "success": True,
            "data": result,
            "error": None,
        }

    except ValueError as e:
        logger.warning("submit_quiz: scoring error for %s: %s", user_id, e)
        return {
            "success": False,
            "data": None,
            "error": "Please check your answers and try again.",
        }
    except Exception:
        logger.error("submit_quiz: unexpected error for %s", user_id, exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }
