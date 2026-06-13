"""India localisation tests — I18N-01 through I18N-20.

Verifies emission factor values are India-specific, that all Indian commute
modes and diet types are present, that personas cover Indian demographics,
and that analogy strings are localised (km, not miles).

No mocking needed for emission factor tests — pure imports.
Firebase auth is mocked for the constants endpoint tests (I18N-19–20).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

from unittest.mock import MagicMock, patch

from constants.emission_factors import EMISSION_FACTORS
from utils.calculator import calculate_daily_score
from utils.analogy_engine import get_analogy
from models.requests import CommuteModeEnum, DietTypeEnum, PersonaEnum

# ── I18N-01 ───────────────────────────────────────────────────────────────────

def test_i18n_01_grid_factor_is_india_cea_value():
    """I18N-01: electricity.grid_factor == 0.82 (India CEA 2023 average)."""
    assert EMISSION_FACTORS["electricity"]["grid_factor"] == 0.82


# ── I18N-02 ───────────────────────────────────────────────────────────────────

def test_i18n_02_petrol_car_factor():
    """I18N-02: transport.petrol_car == 0.17 kg CO2/km."""
    assert EMISSION_FACTORS["transport"]["petrol_car"] == 0.17


def test_i18n_02b_diesel_car_factor():
    """I18N-02b: transport.diesel_car == 0.15 kg CO2/km."""
    assert EMISSION_FACTORS["transport"]["diesel_car"] == 0.15


# ── I18N-03 ───────────────────────────────────────────────────────────────────

def test_i18n_03_petrol_two_wheeler_factor():
    """I18N-03: transport.petrol_two_wheeler == 0.05 kg CO2/km."""
    assert EMISSION_FACTORS["transport"]["petrol_two_wheeler"] == 0.05


# ── I18N-04 ───────────────────────────────────────────────────────────────────

def test_i18n_04_auto_rickshaw_factor():
    """I18N-04: transport.auto_rickshaw == 0.07 kg CO2/km (per passenger)."""
    assert EMISSION_FACTORS["transport"]["auto_rickshaw"] == 0.07


# ── I18N-05 ───────────────────────────────────────────────────────────────────

def test_i18n_05_metro_factor():
    """I18N-05: transport.metro == 0.01 kg CO2/km (per passenger)."""
    assert EMISSION_FACTORS["transport"]["metro"] == 0.01


# ── I18N-06 ───────────────────────────────────────────────────────────────────

def test_i18n_06_lpg_cylinder_co2():
    """I18N-06: lpg.kg_co2_per_cylinder == 12.0 (standard 14.2 kg LPG cylinder)."""
    assert EMISSION_FACTORS["lpg"]["kg_co2_per_cylinder"] == 12.0


# ── I18N-07 ───────────────────────────────────────────────────────────────────

def test_i18n_07_non_vegetarian_diet():
    """I18N-07: diet.non_vegetarian == 5.0 kg CO2/day."""
    assert EMISSION_FACTORS["diet"]["non_vegetarian"] == 5.0


# ── I18N-08 ───────────────────────────────────────────────────────────────────

def test_i18n_08_auto_rickshaw_in_commute_enum():
    """I18N-08: auto_rickshaw is a valid CommuteModeEnum value."""
    assert "auto_rickshaw" in [m.value for m in CommuteModeEnum]


# ── I18N-09 ───────────────────────────────────────────────────────────────────

def test_i18n_09_diesel_car_in_commute_enum():
    """I18N-09: diesel_car is a valid CommuteModeEnum value."""
    assert "diesel_car" in [m.value for m in CommuteModeEnum]


# ── I18N-10 ───────────────────────────────────────────────────────────────────

def test_i18n_10_walking_and_cycling_produce_diet_only_score():
    """I18N-10: walking and cycling → 0 transport CO2 → diet-only score."""
    profile_walk = {
        "commute_mode": "walking",
        "avg_daily_km": 10.0,
        "diet_type": "vegan",
        "ac_hours_per_day": 0.0,
    }
    profile_cycle = {**profile_walk, "commute_mode": "cycling"}

    score_walk = calculate_daily_score(profile_walk)
    score_cycle = calculate_daily_score(profile_cycle)
    vegan_diet = EMISSION_FACTORS["diet"]["vegan"]

    assert score_walk == round(vegan_diet, 2)
    assert score_cycle == round(vegan_diet, 2)


# ── I18N-11 ───────────────────────────────────────────────────────────────────

def test_i18n_11_eggetarian_in_diet_enum():
    """I18N-11: eggetarian is a valid DietTypeEnum value."""
    assert "eggetarian" in [d.value for d in DietTypeEnum]


# ── I18N-12 ───────────────────────────────────────────────────────────────────

def test_i18n_12_eggetarian_score_between_veg_and_non_veg():
    """I18N-12: eggetarian score lies between vegetarian and non_vegetarian."""
    base_profile = {
        "commute_mode": "walking",
        "avg_daily_km": 0.0,
        "ac_hours_per_day": 0.0,
    }
    score_veg = calculate_daily_score({**base_profile, "diet_type": "vegetarian"})
    score_egg = calculate_daily_score({**base_profile, "diet_type": "eggetarian"})
    score_nveg = calculate_daily_score({**base_profile, "diet_type": "non_vegetarian"})

    assert score_veg < score_egg < score_nveg


# ── I18N-13 ───────────────────────────────────────────────────────────────────

def test_i18n_13_diet_ordering_vegan_lt_vegetarian_lt_eggetarian_lt_nonveg():
    """I18N-13: vegan < vegetarian < eggetarian < non_vegetarian — ordering correct."""
    d = EMISSION_FACTORS["diet"]
    assert d["vegan"] < d["vegetarian"] < d["eggetarian"] < d["non_vegetarian"]


# ── I18N-14 ───────────────────────────────────────────────────────────────────

def test_i18n_14_all_5_personas_in_allowlist():
    """I18N-14: All 5 Indian personas present in PersonaEnum."""
    personas = {p.value for p in PersonaEnum}
    assert "student" in personas
    assert "professional" in personas
    assert "family" in personas
    assert "teenager" in personas
    assert "senior" in personas


# ── I18N-15 ───────────────────────────────────────────────────────────────────

def test_i18n_15_student_suggestions_reference_campus():
    """I18N-15: Student persona suggestions reference campus or canteen."""
    from utils.suggestion_engine import get_rule_based_suggestions
    profile = {
        "commute_mode": "bus",
        "avg_daily_km": 5.0,
        "diet_type": "non_vegetarian",
        "ac_hours_per_day": 0.0,
        "lpg_cylinders_per_month": 0.0,
    }
    suggestions = get_rule_based_suggestions(profile, persona="student")
    combined = " ".join(suggestions).lower()
    assert "campus" in combined or "canteen" in combined or "college" in combined or "hostel" in combined


# ── I18N-16 ───────────────────────────────────────────────────────────────────

def test_i18n_16_family_suggestions_reference_lpg_or_household():
    """I18N-16: Family persona suggestions reference LPG or household."""
    from utils.suggestion_engine import get_rule_based_suggestions
    profile = {
        "commute_mode": "petrol_car",
        "avg_daily_km": 20.0,
        "diet_type": "non_vegetarian",
        "ac_hours_per_day": 4.0,
        "lpg_cylinders_per_month": 2.0,
    }
    suggestions = get_rule_based_suggestions(profile, persona="family")
    combined = " ".join(suggestions).lower()
    assert (
        "lpg" in combined
        or "household" in combined
        or "family" in combined
        or "home" in combined
        or "cylinder" in combined
    )


# ── I18N-17 ───────────────────────────────────────────────────────────────────

def test_i18n_17_1kg_analogy_uses_indian_references_not_miles():
    """I18N-17: 1 kg analogy does not contain 'miles' — km or Indian references only."""
    analogy = get_analogy(1.0)
    assert "mile" not in analogy.lower()
    # Should reference something recognisable in Indian context
    assert isinstance(analogy, str)
    assert len(analogy) > 0


# ── I18N-18 ───────────────────────────────────────────────────────────────────

def test_i18n_18_no_mile_substring_in_any_analogy():
    """I18N-18: 'mile' never appears in any analogy output for standard values."""
    test_values = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]
    for co2_kg in test_values:
        analogy = get_analogy(co2_kg)
        assert "mile" not in analogy.lower(), (
            f"'mile' found in analogy for {co2_kg} kg: {analogy}"
        )


# ── I18N-19 & I18N-20 ────────────────────────────────────────────────────────

def test_i18n_19_constants_endpoint_returns_full_emission_factors():
    """I18N-19: GET /api/constants returns full EMISSION_FACTORS — all keys present."""
    with (
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get("/api/constants")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    constants = body["data"]["constants"]
    assert "transport" in constants
    assert "diet" in constants
    assert "electricity" in constants
    assert "lpg" in constants


def test_i18n_20_constants_endpoint_matches_emission_factors_exactly():
    """I18N-20: /api/constants response matches EMISSION_FACTORS exactly — deep equality."""
    with (
        patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}),
    ):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get("/api/constants")

    constants = response.json()["data"]["constants"]
    assert constants["transport"] == EMISSION_FACTORS["transport"]
    assert constants["diet"] == EMISSION_FACTORS["diet"]
    assert constants["electricity"] == EMISSION_FACTORS["electricity"]
    assert constants["lpg"] == EMISSION_FACTORS["lpg"]
