"""Profile utility functions — converts and merges Pydantic request models to Firestore dicts.

Extracted from routes/user.py to keep routes thin (CODING_STANDARDS.md §1.8).
Pure functions — no DB access, no API calls.
"""

# Internal — request models
from models.requests import OnboardingRequest, ProfileUpdateRequest


def profile_from_request(body: OnboardingRequest) -> dict:
    """Convert a validated OnboardingRequest into a plain dict for Firestore storage.

    Enum values are already resolved to strings by Pydantic (use_enum_values=True),
    so the returned dict is JSON- and Firestore-safe with no further conversion.

    Args:
        body: Validated OnboardingRequest from Pydantic.

    Returns:
        Dict representation of the user profile.

    Raises:
        ValueError: If any required attribute is missing from the request body.
    """
    try:
        return {
            "name": body.name,
            "state": body.state,
            "city": body.city,
            "commute_mode": body.commute_mode,
            "avg_daily_km": body.avg_daily_km,
            "diet_type": body.diet_type,
            "ac_hours_per_day": body.ac_hours_per_day,
            "lpg_cylinders_per_month": body.lpg_cylinders_per_month,
            "persona": body.persona,
        }
    except AttributeError as e:
        raise ValueError(f"profile_from_request: missing field on request body — {e}") from e
    except Exception as e:
        raise ValueError(f"profile_from_request: unexpected error — {e}") from e


def merge_profile(existing: dict, update: ProfileUpdateRequest) -> dict:
    """Merge non-None fields from a ProfileUpdateRequest into an existing profile dict.

    Uses model_dump(exclude_none=True) so only explicitly supplied fields overwrite
    the existing values — absent (None) fields leave the original data intact.

    Args:
        existing: Current profile dict from Firestore.
        update:   Validated ProfileUpdateRequest; fields may be None (= no change).

    Returns:
        New merged dict with updated fields applied over the existing profile.

    Raises:
        ValueError: If existing is not a dict or update cannot be dumped.
    """
    try:
        if not isinstance(existing, dict):
            raise ValueError(
                f"merge_profile: existing must be a dict, got {type(existing).__name__}"
            )
        merged = dict(existing)
        update_data = update.model_dump(exclude_none=True)
        merged.update(update_data)
        return merged
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"merge_profile: unexpected error — {e}") from e
