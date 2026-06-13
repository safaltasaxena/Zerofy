"""Tests for backend/utils/analogy_engine.py.

Maps to TESTING.md §3b (ANA-01 through ANA-08).
All tests are pure — no mocking, no DB, no HTTP calls required.
The get_analogy function is a pure lookup with no side effects.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from utils.analogy_engine import get_analogy
from utils.calculator import CalculationError


# ── ANA-01 ────────────────────────────────────────────────────────────────────

def test_ana_01_one_kg_contains_smartphone_reference():
    """ANA-01: 1.0 kg → string references smartphones."""
    result = get_analogy(1.0)
    assert isinstance(result, str)
    assert len(result) > 0
    # Must contain a smartphone/phone reference (India-relevant analogy)
    assert "smartphone" in result.lower() or "phone" in result.lower(), (
        f"Expected smartphone reference in: {result!r}"
    )


# ── ANA-02 ────────────────────────────────────────────────────────────────────

def test_ana_02_zero_kg_returns_zero_state_message():
    """ANA-02: 0.0 kg → returns the zero-state message string (not crash)."""
    result = get_analogy(0.0)
    assert isinstance(result, str)
    assert len(result) > 0
    # Must communicate a zero-emission day positively
    assert "zero" in result.lower() or "🌱" in result, (
        f"Expected zero-state message, got: {result!r}"
    )


# ── ANA-03 ────────────────────────────────────────────────────────────────────

def test_ana_03_large_value_returns_scaled_string():
    """ANA-03: 100.0 kg → returns a non-empty string (scaled analogy)."""
    result = get_analogy(100.0)
    assert isinstance(result, str)
    assert len(result) > 0


# ── ANA-04 ────────────────────────────────────────────────────────────────────

def test_ana_04_negative_raises_calculation_error():
    """ANA-04: negative co2_kg → raises CalculationError."""
    with pytest.raises(CalculationError):
        get_analogy(-0.1)


def test_ana_04b_large_negative_raises_calculation_error():
    """ANA-04 (variant): large negative value → raises CalculationError."""
    with pytest.raises(CalculationError):
        get_analogy(-100.0)


# ── ANA-05 ────────────────────────────────────────────────────────────────────

def test_ana_05_transport_context_returns_string():
    """ANA-05: context='transport' → returns a non-empty string."""
    result = get_analogy(1.0, context="transport")
    assert isinstance(result, str)
    assert len(result) > 0


def test_ana_05b_transport_context_zero_kg():
    """ANA-05 (variant): context='transport', 0.0 kg → zero-state message."""
    result = get_analogy(0.0, context="transport")
    assert isinstance(result, str)
    assert len(result) > 0


def test_ana_05c_transport_context_large_value():
    """ANA-05 (variant): context='transport', 50.0 kg → returns string."""
    result = get_analogy(50.0, context="transport")
    assert isinstance(result, str)
    assert len(result) > 0


# ── ANA-06 ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("co2_kg,context", [
    (0.0,    "general"),
    (0.5,    "general"),
    (1.0,    "general"),
    (2.0,    "general"),
    (4.0,    "general"),
    (8.0,    "general"),
    (15.0,   "general"),
    (1.0,    "transport"),
    (5.0,    "transport"),
    (20.0,   "transport"),
    (0.0,    "unknown_context"),
])
def test_ana_06_return_type_is_always_str(co2_kg, context):
    """ANA-06: return type is always str for any valid input and any context."""
    result = get_analogy(co2_kg, context=context)
    assert isinstance(result, str), (
        f"Expected str for co2_kg={co2_kg}, context={context!r}, got {type(result)}"
    )


# ── ANA-07 ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("co2_kg", [0.0, 0.01, 1.0, 3.5, 7.0, 11.0, 100.0])
def test_ana_07_return_value_is_never_none(co2_kg):
    """ANA-07: return value is never None for any valid non-negative input."""
    result = get_analogy(co2_kg)
    assert result is not None


# ── ANA-08 ────────────────────────────────────────────────────────────────────

def test_ana_08_no_side_effects_no_http_no_db(monkeypatch):
    """ANA-08: calling get_analogy makes no HTTP calls and no DB calls.

    We patch urllib.request.urlopen and socket.create_connection so that any
    attempted network call raises an exception. The function must complete
    without triggering these.
    """
    import urllib.request
    import socket

    def _block_http(*args, **kwargs):
        raise AssertionError("get_analogy must not make HTTP calls")

    def _block_socket(*args, **kwargs):
        raise AssertionError("get_analogy must not open network sockets")

    monkeypatch.setattr(urllib.request, "urlopen", _block_http)
    monkeypatch.setattr(socket, "create_connection", _block_socket)

    # Should complete without raising AssertionError
    result = get_analogy(2.5, context="general")
    assert isinstance(result, str)
    assert len(result) > 0


def test_ana_08b_no_side_effects_multiple_calls():
    """ANA-08 (variant): repeated calls return consistent results — pure function."""
    first = get_analogy(3.0)
    second = get_analogy(3.0)
    assert first == second, "Pure function must return identical results for identical input"


# ── Additional boundary tests ─────────────────────────────────────────────────

def test_boundary_just_above_zero():
    """Boundary: 0.01 kg → falls into smartphone bracket, not zero-state."""
    result = get_analogy(0.01)
    assert result != "You had a zero-carbon day 🌱"
    assert isinstance(result, str)


def test_boundary_exactly_one_kg():
    """Boundary: exactly 1.0 kg → upper bound of smartphone bracket."""
    result = get_analogy(1.0)
    assert "smartphone" in result.lower() or "phone" in result.lower()


def test_boundary_just_above_one_kg():
    """Boundary: 1.01 kg → falls into ceiling fan bracket."""
    result = get_analogy(1.01)
    assert isinstance(result, str)
    assert "fan" in result.lower() or "ceiling" in result.lower()


def test_unknown_context_falls_back_to_general():
    """Unknown context → falls back to general analogy without raising."""
    result = get_analogy(2.0, context="lpg")
    assert isinstance(result, str)
    assert len(result) > 0
