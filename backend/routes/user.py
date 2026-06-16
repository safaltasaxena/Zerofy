"""User routes — onboarding, profile read, and profile update.

Routes are thin: validate input → call utils → read/write Firestore → return response.
No business logic lives here. All carbon math is in utils/calculator.py.
Profile conversion/merging is in utils/profile_utils.py.

Firestore collection: profiles/{user_id}
"""

# Standard library
import logging

# Third-party
from fastapi import APIRouter, Depends

# Internal — auth
from middleware.auth import verify_token

# Internal — Firestore (module-level import per FIX 2; alias preserves test patch target)
from config import firebase
get_db = firebase.get_db  # module-level alias — patch target: routes.user.get_db

# Internal — request models
from models.requests import OnboardingRequest, ProfileUpdateRequest

# Internal — profile utilities
from utils.profile_utils import profile_from_request, merge_profile

# Internal — calculation utils
from utils.calculator import calculate_daily_score, calculate_breakdown, CalculationError
from utils.analogy_engine import get_analogy

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])

_PROFILES_COLLECTION: str = "profiles"


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/user/onboarding")
async def onboarding(
    body: OnboardingRequest,
    user_id: str = Depends(verify_token),
) -> dict:
    """Create or replace a user's profile and calculate their baseline daily CO2.

    Saves the profile to profiles/{user_id} in Firestore.
    Calculates the daily carbon footprint score using calculator.py.

    Args:
        body:    Validated onboarding data from the request body.
        user_id: Verified uid from Firebase token — never from request body.

    Returns:
        Standard response: {success, data: {daily_co2_kg, profile}}.
    """
    try:
        profile = profile_from_request(body)
        daily_co2_kg = calculate_daily_score(profile)
        breakdown = calculate_breakdown(profile)

        profile["baseline_daily_co2_kg"] = daily_co2_kg
        profile["baseline_monthly_co2_kg"] = round(daily_co2_kg * 30, 2)
        profile["score_breakdown"] = breakdown
        profile["baseline_analogy"] = get_analogy(daily_co2_kg)

        db = get_db()
        db.collection(_PROFILES_COLLECTION).document(user_id).set(profile)

        return {
            "success": True,
            "data": {"daily_co2_kg": daily_co2_kg, "profile": profile},
            "error": None,
        }

    except CalculationError as e:
        logger.warning("onboarding: calculation error for %s: %s", user_id, e)
        return {
            "success": False,
            "data": None,
            "error": "Could not calculate your carbon score. Please check your input.",
        }
    except Exception:
        logger.error("onboarding: unexpected error for %s", user_id, exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }


@router.get("/user/profile")
async def get_profile(
    user_id: str = Depends(verify_token),
) -> dict:
    """Retrieve the authenticated user's profile from Firestore.

    Args:
        user_id: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {profile}}.
    """
    try:
        db = get_db()
        doc = db.collection(_PROFILES_COLLECTION).document(user_id).get()

        if not doc.exists:
            return {
                "success": False,
                "data": None,
                "error": "Profile not found. Please complete onboarding.",
            }

        profile = doc.to_dict() or {}
        if "baseline_daily_co2_kg" in profile:
            profile["baseline_analogy"] = get_analogy(profile["baseline_daily_co2_kg"])

        return {
            "success": True,
            "data": {"profile": profile},
            "error": None,
        }

    except Exception:
        logger.error("get_profile: unexpected error for %s", user_id, exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }


@router.put("/user/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(verify_token),
) -> dict:
    """Merge a partial profile update and recalculate the daily CO2 score.

    Only fields present in the request body are updated; all others retain
    their existing values. Recalculates daily_co2_kg after the merge.

    Args:
        body:    Partial profile update — only non-None fields are applied.
        user_id: Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {daily_co2_kg, profile}}.
    """
    try:
        db = get_db()
        doc = db.collection(_PROFILES_COLLECTION).document(user_id).get()

        if not doc.exists:
            return {
                "success": False,
                "data": None,
                "error": "Profile not found. Please complete onboarding first.",
            }

        existing = doc.to_dict() or {}
        merged = merge_profile(existing, body)

        daily_co2_kg = calculate_daily_score(merged)
        breakdown = calculate_breakdown(merged)

        merged["baseline_daily_co2_kg"] = daily_co2_kg
        merged["baseline_monthly_co2_kg"] = round(daily_co2_kg * 30, 2)
        merged["score_breakdown"] = breakdown
        merged["baseline_analogy"] = get_analogy(daily_co2_kg)

        db.collection(_PROFILES_COLLECTION).document(user_id).set(merged)

        return {
            "success": True,
            "data": {"daily_co2_kg": daily_co2_kg, "profile": merged},
            "error": None,
        }

    except CalculationError as e:
        logger.warning("update_profile: calculation error for %s: %s", user_id, e)
        return {
            "success": False,
            "data": None,
            "error": "Could not recalculate your carbon score. Please check the updated values.",
        }
    except Exception:
        logger.error("update_profile: unexpected error for %s", user_id, exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }
