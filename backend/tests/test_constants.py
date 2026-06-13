"""Constants module tests — CONST-01 through CONST-13.

Tests the EMISSION_FACTORS dict from constants/emission_factors.py directly,
plus the GET /api/constants endpoint for structure and deep equality.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")

import inspect
from unittest.mock import MagicMock, patch
import constants.emission_factors as _ef_module
from constants.emission_factors import EMISSION_FACTORS

_ALL_TRANSPORT_MODES = [
    "petrol_car", "diesel_car", "petrol_two_wheeler", "electric_vehicle",
    "auto_rickshaw", "bus", "metro", "walking", "cycling",
]

_ALL_DIET_TYPES = ["non_vegetarian", "vegetarian", "eggetarian", "vegan"]

# ── CONST-01 ──────────────────────────────────────────────────────────────────

def test_const_01_emission_factors_is_dict():
    """CONST-01: EMISSION_FACTORS is a dict."""
    assert isinstance(EMISSION_FACTORS, dict)


# ── CONST-02 ──────────────────────────────────────────────────────────────────

def test_const_02_all_9_transport_modes_present():
    """CONST-02: All 9 Indian transport modes present in transport section."""
    transport = EMISSION_FACTORS["transport"]
    for mode in _ALL_TRANSPORT_MODES:
        assert mode in transport, f"Missing transport mode: {mode}"


# ── CONST-03 ──────────────────────────────────────────────────────────────────

def test_const_03_all_4_diet_types_present():
    """CONST-03: All 4 diet types present."""
    diet = EMISSION_FACTORS["diet"]
    for diet_type in _ALL_DIET_TYPES:
        assert diet_type in diet, f"Missing diet type: {diet_type}"


# ── CONST-04 ──────────────────────────────────────────────────────────────────

def test_const_04_grid_factor_is_0_82():
    """CONST-04: electricity.grid_factor == 0.82 (India CEA)."""
    assert EMISSION_FACTORS["electricity"]["grid_factor"] == 0.82


# ── CONST-05 ──────────────────────────────────────────────────────────────────

def test_const_05_no_function_definitions_in_module():
    """CONST-05: emission_factors.py is pure data — no function definitions."""
    functions = [
        name for name, obj in inspect.getmembers(_ef_module)
        if inspect.isfunction(obj) and obj.__module__ == _ef_module.__name__
    ]
    assert functions == [], f"Unexpected functions found: {functions}"


# ── CONST-06 ──────────────────────────────────────────────────────────────────

def test_const_06_get_constants_returns_200():
    """CONST-06: GET /api/constants returns 200 with success: true."""
    with patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get("/api/constants")

    assert response.status_code == 200
    assert response.json()["success"] is True


# ── CONST-07 ──────────────────────────────────────────────────────────────────

def test_const_07_response_matches_emission_factors_deep_equality():
    """CONST-07: GET /api/constants data.constants matches EMISSION_FACTORS exactly."""
    with patch("firebase_admin._apps", {"[DEFAULT]": MagicMock()}):
        from main import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        response = client.get("/api/constants")

    constants = response.json()["data"]["constants"]
    assert constants == EMISSION_FACTORS


# ── CONST-08 ──────────────────────────────────────────────────────────────────

def test_const_08_all_values_are_numeric():
    """CONST-08: All leaf values in EMISSION_FACTORS are float or int — no strings."""
    def _check_all_numeric(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _check_all_numeric(v, f"{path}.{k}")
        elif not isinstance(obj, (int, float)):
            raise AssertionError(
                f"Non-numeric value at {path}: {type(obj).__name__} = {obj!r}"
            )

    _check_all_numeric(EMISSION_FACTORS)


# ── CONST-09 ──────────────────────────────────────────────────────────────────

def test_const_09_all_emission_values_non_negative():
    """CONST-09: All values >= 0 — no negative emission factors."""
    def _check_non_negative(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _check_non_negative(v, f"{path}.{k}")
        elif isinstance(obj, (int, float)):
            assert obj >= 0, f"Negative value at {path}: {obj}"

    _check_non_negative(EMISSION_FACTORS)


# ── CONST-10 ──────────────────────────────────────────────────────────────────

def test_const_10_walking_and_cycling_are_zero():
    """CONST-10: walking and cycling transport factors == 0.0."""
    assert EMISSION_FACTORS["transport"]["walking"] == 0.0
    assert EMISSION_FACTORS["transport"]["cycling"] == 0.0


# ── CONST-11 ──────────────────────────────────────────────────────────────────

def test_const_11_grid_factor_in_valid_range():
    """CONST-11: grid_factor is between 0.7 and 1.0 (plausible India CEA range)."""
    gf = EMISSION_FACTORS["electricity"]["grid_factor"]
    assert 0.7 <= gf <= 1.0


# ── CONST-12 ──────────────────────────────────────────────────────────────────

def test_const_12_petrol_car_greater_than_electric():
    """CONST-12: petrol_car emission > electric_vehicle."""
    t = EMISSION_FACTORS["transport"]
    assert t["petrol_car"] > t["electric_vehicle"]


# ── CONST-13 ──────────────────────────────────────────────────────────────────

def test_const_13_non_vegetarian_greater_than_vegan():
    """CONST-13: non_vegetarian diet > vegan diet."""
    d = EMISSION_FACTORS["diet"]
    assert d["non_vegetarian"] > d["vegan"]
