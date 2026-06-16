"""Pydantic request body models for all Zerofy India API endpoints.

All field constraints mirror SECURITY_SPEC.md §4 exactly.
Enum values match EMISSION_FACTORS keys — do not add values here without
updating emission_factors.py first.
"""

# Standard library
from enum import Enum
from typing import Optional

# Third-party
import re
from pydantic import BaseModel, Field, field_validator


# ── Enums — allowlists from SECURITY_SPEC.md §4 ──────────────────────────────

class CommuteModeEnum(str, Enum):
    """Valid commute modes — must match EMISSION_FACTORS["transport"] keys."""
    petrol_car = "petrol_car"
    diesel_car = "diesel_car"
    petrol_two_wheeler = "petrol_two_wheeler"
    electric_vehicle = "electric_vehicle"
    auto_rickshaw = "auto_rickshaw"
    bus = "bus"
    metro = "metro"
    walking = "walking"
    cycling = "cycling"


class DietTypeEnum(str, Enum):
    """Valid diet types — must match EMISSION_FACTORS["diet"] keys."""
    non_vegetarian = "non_vegetarian"
    vegetarian = "vegetarian"
    eggetarian = "eggetarian"
    vegan = "vegan"


class PersonaEnum(str, Enum):
    """Valid user personas — drives Gemini suggestion tone."""
    student = "student"
    professional = "professional"
    family = "family"
    teenager = "teenager"
    senior = "senior"


# ── Request models ────────────────────────────────────────────────────────────

class OnboardingRequest(BaseModel):
    """Request body for POST /api/user/onboarding.

    All fields required. Constraints follow SECURITY_SPEC.md §4.
    """

    name: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    city: str = Field(..., min_length=2, max_length=50)
    commute_mode: CommuteModeEnum
    avg_daily_km: float = Field(..., ge=0.0, le=500.0)
    diet_type: DietTypeEnum
    ac_hours_per_day: float = Field(..., ge=0.0, le=24.0)
    lpg_cylinders_per_month: float = Field(..., ge=0.0, le=10.0)
    monthly_electricity_units: float = Field(..., ge=0.0, le=10000.0)
    persona: PersonaEnum

    model_config = {"use_enum_values": True}


class ProfileUpdateRequest(BaseModel):
    """Request body for PUT /api/user/profile — all fields optional (partial update).

    Only supplied fields will be merged into the existing profile.
    Constraints are identical to OnboardingRequest.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    city: Optional[str] = Field(None, min_length=2, max_length=50)
    commute_mode: Optional[CommuteModeEnum] = None
    avg_daily_km: Optional[float] = Field(None, ge=0.0, le=500.0)
    diet_type: Optional[DietTypeEnum] = None
    ac_hours_per_day: Optional[float] = Field(None, ge=0.0, le=24.0)
    lpg_cylinders_per_month: Optional[float] = Field(None, ge=0.0, le=10.0)
    monthly_electricity_units: Optional[float] = Field(None, ge=0.0, le=10000.0)
    persona: Optional[PersonaEnum] = None

    model_config = {"use_enum_values": True}


class ChatUpdateRequest(BaseModel):
    """Request body for POST /api/logs/chat-update.

    Message length cap mirrors SECURITY_SPEC.md §4 and gemini_parser truncation.
    Whitespace is stripped before validation. HTML tags are rejected at this layer.
    """

    message: str = Field(..., min_length=1, max_length=500)

    @field_validator("message", mode="before")
    @classmethod
    def strip_and_reject_html(cls, v: str) -> str:
        """Strip leading/trailing whitespace, reject empty and HTML-containing messages."""
        if not isinstance(v, str):
            raise ValueError("message must be a string")
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty or whitespace only")
        if re.search(r"<[a-zA-Z]", v):
            raise ValueError("message must not contain HTML tags")
        return v
