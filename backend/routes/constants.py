"""Constants route — serves EMISSION_FACTORS as JSON to the frontend.

Public endpoint — no auth required (SECURITY_SPEC.md §5).
EFFICIENCY.md: Simulator calculations run on the frontend using this data,
so no Gemini call and no backend math is required here.
"""

# Standard library
import logging

# Third-party
from fastapi import APIRouter

# Internal
from constants.emission_factors import EMISSION_FACTORS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["constants"])


@router.get("/constants")
async def get_constants() -> dict:
    """Return the full EMISSION_FACTORS dict — single source of truth for the frontend.

    No authentication required. Serves all CO2 multipliers used by the
    simulator and frontend carbon math.

    Returns:
        Standard response: {success, data: {constants}}.
    """
    try:
        return {
            "success": True,
            "data": {"constants": EMISSION_FACTORS},
            "error": None,
        }
    except Exception:
        logger.error("get_constants: unexpected error", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": "Something went wrong. Please try again.",
        }
