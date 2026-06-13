"""Simulator route — validates a what-if profile and returns scores.

Per EFFICIENCY.md §3: live slider math runs entirely in the browser using
constants from /api/constants. This endpoint is for validation only and
is NEVER called during slider movement.

No Gemini calls. No Firestore reads or writes.
"""

# Standard library
import logging

# Third-party
from fastapi import APIRouter, Depends, Query

# Internal — auth
from middleware.auth import verify_token

# Internal — calculation utils
from utils.calculator import (
    CalculationError,
    calculate_breakdown,
    calculate_daily_score,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["simulator"])

# ── Allowed enum values — duplicated from models for query-param validation ──
# Cannot use Pydantic models directly on GET query params with enum types;
# validation is done manually to keep the route thin.

_VALID_COMMUTE_MODES: frozenset[str] = frozenset({
    "petrol_car", "diesel_car", "petrol_two_wheeler", "electric_vehicle",
    "auto_rickshaw", "bus", "metro", "walking", "cycling",
})

_VALID_DIET_TYPES: frozenset[str] = frozenset({
    "non_vegetarian", "vegetarian", "eggetarian", "vegan",
})


@router.get("/simulator/calculate")
async def simulator_calculate(
    commute_mode: str = Query(..., description="User's commute mode"),
    avg_daily_km: float = Query(..., ge=0.0, le=500.0, description="km per day"),
    diet_type: str = Query(..., description="User's diet type"),
    ac_hours_per_day: float = Query(..., ge=0.0, le=24.0, description="AC hours per day"),
    lpg_cylinders_per_month: float = Query(..., ge=0.0, le=10.0, description="LPG cylinders/month"),
    token_uid: str = Depends(verify_token),
) -> dict:
    """Validate a what-if habit profile and return the calculated carbon score.

    Called by the simulator when the user wants to confirm a scenario —
    NOT during live slider movement (which uses pure frontend math).

    All calculations are pure math — no Gemini, no Firestore.

    Args:
        commute_mode:            Transport mode string.
        avg_daily_km:            Daily commute distance in km (0–500).
        diet_type:               Diet type string.
        ac_hours_per_day:        AC usage in hours (0–24).
        lpg_cylinders_per_month: LPG usage in cylinders/month (0–10).
        token_uid:               Verified uid from Firebase token.

    Returns:
        Standard response: {success, data: {daily_co2_kg, breakdown}}.
    """
    try:
        # Validate enum query params (cannot use Pydantic enum on Query directly)
        if commute_mode not in _VALID_COMMUTE_MODES:
            return {
                "success": False,
                "data": None,
                "error": "Please check your input and try again.",
            }
        if diet_type not in _VALID_DIET_TYPES:
            return {
                "success": False,
                "data": None,
                "error": "Please check your input and try again.",
            }

        profile = {
            "commute_mode": commute_mode,
            "avg_daily_km": avg_daily_km,
            "diet_type": diet_type,
            "ac_hours_per_day": ac_hours_per_day,
            "lpg_cylinders_per_month": lpg_cylinders_per_month,
        }

        daily_co2_kg = calculate_daily_score(profile)
        breakdown = calculate_breakdown(profile)

        return {
            "success": True,
            "data": {
                "daily_co2_kg": daily_co2_kg,
                "breakdown": breakdown,
            },
            "error": None,
        }

    except CalculationError as e:
        logger.warning("simulator_calculate: calculation error: %s", e)
        return {
            "success": False,
            "data": None,
            "error": "Please check your input and try again.",
        }
    except Exception:
        logger.error("simulator_calculate: unexpected error", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }
