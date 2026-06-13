"""Tests for backend/utils/calculator.py.

Maps to TESTING.md §3a (CALC-01 through CALC-12) and §10 edge cases (EDGE-01 through EDGE-06).
All tests are pure math — no mocking, no DB, no external calls required.

NOTE on CALC-01 expected value:
  The arithmetic is: 0.17×10 + 5.0 + 0.82×1.5×2 = 9.16 kg
  The test asserts 9.16.
"""

import sys
import os

# Allow running from the backend/ directory or the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from utils.calculator import (
    CalculationError,
    calculate_breakdown,
    calculate_daily_score,
    calculate_delta,
    calculate_electricity_emission,
    calculate_diet_emission,
    calculate_monthly_score,
    calculate_transport_emission,
    simulate_changes,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def profile_petrol_non_veg_ac() -> dict:
    """Standard profile: petrol_car, 10 km, non-vegetarian, 2 AC hours."""
    return {
        "commute_mode": "petrol_car",
        "avg_daily_km": 10.0,
        "diet_type": "non_vegetarian",
        "ac_hours_per_day": 2.0,
    }


@pytest.fixture
def profile_walking_vegan_no_ac() -> dict:
    """Zero-transport profile: walking, 0 km, vegan, no AC."""
    return {
        "commute_mode": "walking",
        "avg_daily_km": 0.0,
        "diet_type": "vegan",
        "ac_hours_per_day": 0.0,
    }


@pytest.fixture
def profile_metro_veg_no_ac() -> dict:
    """Metro commuter: metro, 8 km, vegetarian, no AC."""
    return {
        "commute_mode": "metro",
        "avg_daily_km": 8.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }


@pytest.fixture
def profile_diesel_non_veg_no_ac() -> dict:
    """Diesel car: 10 km, non-vegetarian, no AC."""
    return {
        "commute_mode": "diesel_car",
        "avg_daily_km": 10.0,
        "diet_type": "non_vegetarian",
        "ac_hours_per_day": 0.0,
    }


# ── CALC-01 ───────────────────────────────────────────────────────────────────

def test_calc_01_petrol_car_non_veg_ac(profile_petrol_non_veg_ac):
    """CALC-01: petrol_car 10km, non-veg, 2 AC hours.

    Formula: 0.17×10 + 5.0 + 0.82×1.5×2
           = 1.70   + 5.0 + 2.46
           = 9.16 kg
    (TESTING.md annotation contains an arithmetic error — result is 9.16 not 8.16.)
    """
    result = calculate_daily_score(profile_petrol_non_veg_ac)
    assert result == pytest.approx(9.16, abs=0.01)


# ── CALC-02 ───────────────────────────────────────────────────────────────────

def test_calc_02_walking_vegan_no_ac(profile_walking_vegan_no_ac):
    """CALC-02: walking 0 km, vegan, no AC → diet-only = 1.5 kg."""
    result = calculate_daily_score(profile_walking_vegan_no_ac)
    assert result == pytest.approx(1.5, abs=0.01)


# ── CALC-03 ───────────────────────────────────────────────────────────────────

def test_calc_03_metro_vegetarian_no_ac(profile_metro_veg_no_ac):
    """CALC-03: metro 8 km, vegetarian, no AC → 0.01×8 + 2.5 = 2.58 kg."""
    result = calculate_daily_score(profile_metro_veg_no_ac)
    assert result == pytest.approx(2.58, abs=0.01)


# ── CALC-04 / CALC-12 ─────────────────────────────────────────────────────────

def test_calc_04_diesel_car_non_veg_no_ac(profile_diesel_non_veg_no_ac):
    """CALC-04 & CALC-12: diesel_car 10 km, non-veg, no AC → 0.15×10 + 5.0 = 6.5 kg."""
    result = calculate_daily_score(profile_diesel_non_veg_no_ac)
    assert result == pytest.approx(6.5, abs=0.01)


# ── CALC-05 ───────────────────────────────────────────────────────────────────

def test_calc_05_monthly_score():
    """CALC-05: calculate_monthly_score(5.0) → 150.0 kg."""
    result = calculate_monthly_score(5.0)
    assert result == pytest.approx(150.0, abs=0.01)


# ── CALC-06 ───────────────────────────────────────────────────────────────────

def test_calc_06_delta_saving():
    """CALC-06: old=8.16, new=2.58 → -5.58 (saving is NEGATIVE per TESTING.md).

    Formula: new - old = 2.58 - 8.16 = -5.58
    """
    result = calculate_delta(8.16, 2.58)
    assert result == pytest.approx(-5.58, abs=0.01)


# ── CALC-07 ───────────────────────────────────────────────────────────────────

def test_calc_07_delta_increase():
    """CALC-07: old=2.58, new=8.16 → +5.58 (increase is POSITIVE per TESTING.md).

    Formula: new - old = 8.16 - 2.58 = +5.58
    """
    result = calculate_delta(2.58, 8.16)
    assert result == pytest.approx(5.58, abs=0.01)


# ── CALC-08 ───────────────────────────────────────────────────────────────────

def test_calc_08_breakdown_keys_and_total(profile_petrol_non_veg_ac):
    """CALC-08: calculate_breakdown returns dict with all 4 category keys + total.

    All values must be floats and total must equal sum of the 4 parts.
    """
    result = calculate_breakdown(profile_petrol_non_veg_ac)

    # All required keys present
    assert "transport" in result
    assert "diet" in result
    assert "electricity" in result
    assert "lpg" in result
    assert "total" in result

    # All values are numeric (int or float)
    for key, value in result.items():
        assert isinstance(value, (int, float)), f"Key '{key}' is not numeric"

    # Total equals sum of parts (within floating-point tolerance)
    parts_sum = round(
        result["transport"] + result["diet"] + result["electricity"] + result["lpg"],
        2,
    )
    assert parts_sum == pytest.approx(result["total"], abs=0.01)


# ── CALC-09 (re-mapped from TESTING.md CALC-10) ───────────────────────────────

def test_calc_09_missing_commute_mode_raises():
    """CALC-09 (TESTING.md CALC-10 re-mapped): profile missing commute_mode → raises CalculationError."""
    profile = {
        "avg_daily_km": 10.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    with pytest.raises(CalculationError):
        calculate_daily_score(profile)


# ── CALC-09 (new — TESTING.md ARCH §3.3 simulate_changes) ────────────────────

def test_calc_09_simulate_changes_car_to_metro_saves_1_6_kg():
    """CALC-09: simulate_changes switch petrol_car → metro, 10km.

    Expected delta: (0.01 - 0.17) × 10 = -1.6 kg (negative = saving).
    """
    base_profile = {
        "commute_mode": "petrol_car",
        "avg_daily_km": 10.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    result = simulate_changes(base_profile, {"commute_mode": "metro"})

    assert "daily_co2_kg" in result
    assert "breakdown" in result
    assert "delta" in result
    # delta = new - old = -1.6 (saving, because metro emits less)
    assert result["delta"] == pytest.approx(-1.6, abs=0.01)
    # New score must be lower than original
    old_score = calculate_daily_score(base_profile)
    assert result["daily_co2_kg"] < old_score


def test_calc_09_simulate_changes_worsening_returns_positive_delta():
    """CALC-09 variant: switching metro → petrol_car → positive delta (increase)."""
    base_profile = {
        "commute_mode": "metro",
        "avg_daily_km": 10.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    result = simulate_changes(base_profile, {"commute_mode": "petrol_car"})
    assert result["delta"] == pytest.approx(1.6, abs=0.01)


def test_calc_09_simulate_changes_no_change_delta_zero():
    """CALC-09 variant: changes dict is identical → delta == 0.0."""
    profile = {
        "commute_mode": "metro",
        "avg_daily_km": 8.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    result = simulate_changes(profile, {})
    assert result["delta"] == pytest.approx(0.0, abs=0.001)


def test_calc_09_simulate_changes_raises_on_bad_mode():
    """CALC-09 variant: changes with unknown commute_mode → CalculationError."""
    profile = {
        "commute_mode": "metro",
        "avg_daily_km": 5.0,
        "diet_type": "vegan",
        "ac_hours_per_day": 0.0,
    }
    with pytest.raises(CalculationError):
        simulate_changes(profile, {"commute_mode": "rocket"})


# ── CALC-10 (re-mapped from TESTING.md CALC-11) ──────────────────────────────

def test_calc_10_zero_km_valid(profile_walking_vegan_no_ac):
    """CALC-10: avg_daily_km = 0 → no error, returns valid score."""
    profile = {
        "commute_mode": "petrol_car",
        "avg_daily_km": 0.0,
        "diet_type": "vegan",
        "ac_hours_per_day": 0.0,
    }
    result = calculate_daily_score(profile)
    # transport = 0, diet = 1.5, electricity = 0 → 1.5
    assert result == pytest.approx(1.5, abs=0.01)


# ── CALC-11 ───────────────────────────────────────────────────────────────────

def test_calc_11_result_rounded_to_2dp():
    """CALC-11: all results rounded to 2 decimal places."""
    profile = {
        "commute_mode": "petrol_two_wheeler",
        "avg_daily_km": 7.0,
        "diet_type": "eggetarian",
        "ac_hours_per_day": 1.5,
    }
    result = calculate_daily_score(profile)
    # Verify it has at most 2 decimal places
    assert result == round(result, 2)


# ── EDGE-01 ───────────────────────────────────────────────────────────────────

def test_edge_01_zero_km_no_error():
    """EDGE-01: avg_daily_km = 0 → valid result, no division error."""
    profile = {
        "commute_mode": "diesel_car",
        "avg_daily_km": 0.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    result = calculate_daily_score(profile)
    assert isinstance(result, float)
    assert result >= 0


# ── EDGE-02 ───────────────────────────────────────────────────────────────────

def test_edge_02_zero_ac_electricity_is_zero():
    """EDGE-02: ac_hours_per_day = 0 → electricity contribution = 0."""
    result = calculate_electricity_emission(0.0)
    assert result == 0.0


# ── EDGE-03 ───────────────────────────────────────────────────────────────────

def test_edge_03_zero_numeric_habits_returns_diet_only():
    """EDGE-03: walking 0 km, no AC → returns diet-only score (not 0)."""
    profile = {
        "commute_mode": "walking",
        "avg_daily_km": 0.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    result = calculate_daily_score(profile)
    # vegetarian diet = 2.5, transport = 0, electricity = 0
    assert result == pytest.approx(2.5, abs=0.01)
    assert result > 0, "Diet emission must never be zero for a non-zero diet type"


# ── EDGE-04 ───────────────────────────────────────────────────────────────────

def test_edge_04_max_values_valid():
    """EDGE-04: km=500, ac_hours=24 → large but valid float, no error."""
    profile = {
        "commute_mode": "petrol_car",
        "avg_daily_km": 500.0,
        "diet_type": "non_vegetarian",
        "ac_hours_per_day": 24.0,
    }
    result = calculate_daily_score(profile)
    assert isinstance(result, float)
    assert result > 0


# ── EDGE-05 ───────────────────────────────────────────────────────────────────

def test_edge_05_delta_no_change_is_exactly_zero():
    """EDGE-05: calculate_delta(x, x) → 0.0 exactly."""
    result = calculate_delta(5.0, 5.0)
    assert result == 0.0


# ── EDGE-06 ───────────────────────────────────────────────────────────────────

def test_edge_06_unknown_commute_mode_raises_not_silent():
    """EDGE-06: unknown commute_mode raises CalculationError — never silently defaults to 0."""
    with pytest.raises(CalculationError) as exc_info:
        calculate_transport_emission("helicopter", 10.0)
    # Error message must mention the unknown mode
    assert "helicopter" in str(exc_info.value)


def test_edge_06b_unknown_commute_mode_in_daily_score():
    """EDGE-06 (daily_score path): unknown commute_mode raises CalculationError."""
    profile = {
        "commute_mode": "spaceship",
        "avg_daily_km": 10.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
    }
    with pytest.raises(CalculationError):
        calculate_daily_score(profile)
