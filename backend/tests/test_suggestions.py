"""Tests for backend/utils/suggestion_engine.py.

Maps to TESTING.md §3c (SUG-01 through SUG-08) and the Phase-4 PARSE test matrix
(SUG-01 through SUG-12).

ALL AI API calls are mocked — no real network calls are made in any test.
get_rule_based_suggestions is a pure function and requires no mocking.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import MagicMock, patch

from utils.suggestion_engine import (
    SuggestionError,
    get_rule_based_suggestions,
    get_suggestions,
    polish_suggestions,
    _MAX_SUGGESTIONS,
    _SUG_CAR_HIGH_KM,
    _SUG_TWO_WHEELER_HIGH_KM,
    _SUG_EV_OFFPEAK,
    _SUG_DIET_NON_VEG,
    _SUG_AC_HIGH,
    _SUG_AC_MODERATE,
    _SUG_LPG_HIGH,
    _SUG_FALLBACK,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _profile(**overrides) -> dict:
    """Build a minimal valid profile with sensible defaults."""
    base = {
        "commute_mode": "metro",
        "avg_daily_km": 5.0,
        "diet_type": "vegetarian",
        "ac_hours_per_day": 0.0,
        "lpg_cylinders_per_month": 0.5,
    }
    base.update(overrides)
    return base


# ── SUG-01 ────────────────────────────────────────────────────────────────────

def test_sug_01_petrol_car_over_10km_transport_suggestion_present():
    """SUG-01: petrol_car > 10km → transport suggestion is in the list."""
    profile = _profile(commute_mode="petrol_car", avg_daily_km=15.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_CAR_HIGH_KM in result


def test_sug_01_diesel_car_over_10km_transport_suggestion_present():
    """SUG-01 (diesel): diesel_car > 10km → transport suggestion present."""
    profile = _profile(commute_mode="diesel_car", avg_daily_km=11.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_CAR_HIGH_KM in result


def test_sug_01_petrol_car_exactly_10km_no_transport_suggestion():
    """SUG-01 (boundary): petrol_car exactly 10km → rule does NOT fire (> not >=)."""
    profile = _profile(commute_mode="petrol_car", avg_daily_km=10.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_CAR_HIGH_KM not in result


def test_sug_01_metro_no_transport_suggestion():
    """SUG-01 (TESTING.md SUG-02): metro commuter → transport suggestion NOT returned."""
    profile = _profile(commute_mode="metro", avg_daily_km=5.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_CAR_HIGH_KM not in result
    assert _SUG_TWO_WHEELER_HIGH_KM not in result


# ── SUG-02 ────────────────────────────────────────────────────────────────────

def test_sug_02_non_vegetarian_diet_suggestion_present():
    """SUG-02: non_vegetarian diet → diet suggestion to reduce meat is present."""
    profile = _profile(diet_type="non_vegetarian")
    result = get_rule_based_suggestions(profile)
    assert _SUG_DIET_NON_VEG in result


def test_sug_02_vegan_diet_no_diet_warning():
    """SUG-02 (vegan): no diet-reduction suggestion for vegan users."""
    profile = _profile(diet_type="vegan")
    result = get_rule_based_suggestions(profile)
    assert _SUG_DIET_NON_VEG not in result


# ── SUG-03 ────────────────────────────────────────────────────────────────────

def test_sug_03_ac_hours_over_6_high_ac_suggestion():
    """SUG-03: ac_hours_per_day > 6 → high AC suggestion present."""
    profile = _profile(ac_hours_per_day=8.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_AC_HIGH in result


def test_sug_03_ac_hours_exactly_6_does_not_trigger_high():
    """SUG-03 (boundary): ac_hours_per_day = 6.0 → high rule does NOT fire (> not >=)."""
    profile = _profile(ac_hours_per_day=6.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_AC_HIGH not in result


# ── SUG-04 ────────────────────────────────────────────────────────────────────

def test_sug_04_ac_hours_moderate_suggestion():
    """SUG-04: ac_hours_per_day > 3 and ≤ 6 → moderate AC suggestion present."""
    profile = _profile(ac_hours_per_day=5.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_AC_MODERATE in result


def test_sug_04_ac_hours_exactly_3_no_moderate_suggestion():
    """SUG-04 (boundary): ac_hours_per_day = 3.0 → moderate rule does NOT fire."""
    profile = _profile(ac_hours_per_day=3.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_AC_MODERATE not in result


# ── SUG-05 ────────────────────────────────────────────────────────────────────

def test_sug_05_lpg_over_1_suggestion_present():
    """SUG-05: lpg_cylinders_per_month > 1 → LPG suggestion present."""
    profile = _profile(lpg_cylinders_per_month=2.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_LPG_HIGH in result


def test_sug_05_lpg_exactly_1_no_suggestion():
    """SUG-05 (boundary): lpg = 1.0 → rule does NOT fire (> not >=)."""
    profile = _profile(lpg_cylinders_per_month=1.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_LPG_HIGH not in result


# ── SUG-06 ────────────────────────────────────────────────────────────────────

def test_sug_06_all_low_values_fallback_present():
    """SUG-06: all zero/low values → general fallback suggestion present."""
    profile = _profile(
        commute_mode="walking",
        avg_daily_km=0.0,
        diet_type="vegan",
        ac_hours_per_day=0.0,
        lpg_cylinders_per_month=0.0,
    )
    result = get_rule_based_suggestions(profile)
    # With walking + vegan + 0 ac + 0 lpg: only no-ac rule and fallbacks fire
    assert _SUG_FALLBACK in result


# ── SUG-07 ────────────────────────────────────────────────────────────────────

def test_sug_07_always_returns_exactly_3():
    """SUG-07: get_rule_based_suggestions always returns exactly 3 strings."""
    profiles = [
        _profile(),
        _profile(commute_mode="petrol_car", avg_daily_km=20.0,
                 diet_type="non_vegetarian", ac_hours_per_day=8.0,
                 lpg_cylinders_per_month=2.0),
        _profile(commute_mode="walking", avg_daily_km=0.0,
                 diet_type="vegan", ac_hours_per_day=0.0,
                 lpg_cylinders_per_month=0.0),
    ]
    for profile in profiles:
        result = get_rule_based_suggestions(profile)
        assert len(result) == _MAX_SUGGESTIONS, (
            f"Expected {_MAX_SUGGESTIONS} suggestions, got {len(result)}"
        )
        assert all(isinstance(s, str) for s in result)


# ── SUG-08 ────────────────────────────────────────────────────────────────────

def test_sug_08_polish_returns_original_on_gemini_api_failure(monkeypatch):
    """SUG-08: polish_suggestions returns original list on AI failure — does not raise."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["tip one", "tip two", "tip three"]

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.side_effect = Exception("API unreachable")
        result = polish_suggestions(original, "student")

    assert result == original


def test_sug_08_get_suggestions_returns_unpolished_on_gemini_failure(monkeypatch):
    """SUG-08 (get_suggestions path): AI unavailable → returns rule-based suggestions."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    profile = _profile(commute_mode="petrol_car", avg_daily_km=15.0,
                       diet_type="non_vegetarian", ac_hours_per_day=8.0)

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.side_effect = TimeoutError("timeout")
        result = get_suggestions(profile, persona="general")

    assert len(result) == _MAX_SUGGESTIONS
    assert all(isinstance(s, str) for s in result)
    # Must not raise — graceful degradation
    assert _SUG_CAR_HIGH_KM in result
    assert _SUG_DIET_NON_VEG in result


# ── SUG-09 ────────────────────────────────────────────────────────────────────

def test_sug_09_polish_returns_original_on_json_parse_failure(monkeypatch):
    """SUG-09: polish_suggestions returns original on JSON parse failure — does not raise."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["tip one", "tip two", "tip three"]

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.return_value = "this is not valid json at all"
        result = polish_suggestions(original, "professional")

    assert result == original


def test_sug_09_polish_returns_original_on_wrong_array_length(monkeypatch):
    """SUG-09 (variant): AI returns array of wrong length → original returned."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["tip one", "tip two", "tip three"]
    wrong_response = json.dumps(["only one tip"])  # wrong length

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.return_value = wrong_response
        result = polish_suggestions(original, "family")

    assert result == original


def test_sug_09_polish_returns_original_on_non_string_array(monkeypatch):
    """SUG-09 (variant): AI returns array of non-strings → original returned."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["tip one", "tip two", "tip three"]
    bad_response = json.dumps([1, 2, 3])  # numbers, not strings

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.return_value = bad_response
        result = polish_suggestions(original, "teenager")

    assert result == original


# ── SUG-10 ────────────────────────────────────────────────────────────────────

def test_sug_10_get_suggestions_returns_exactly_3(monkeypatch):
    """SUG-10: get_suggestions always returns exactly 3 strings."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    profile = _profile()
    polished = ["polished one", "polished two", "polished three"]

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.return_value = json.dumps(polished)
        result = get_suggestions(profile, persona="professional")

    assert len(result) == _MAX_SUGGESTIONS
    assert result == polished


def test_sug_10_get_suggestions_returns_strings_not_none(monkeypatch):
    """SUG-10 (variant): every item in result is a non-empty string."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.side_effect = Exception("unavailable")
        result = get_suggestions(_profile(), persona="student")

    assert len(result) == _MAX_SUGGESTIONS
    for item in result:
        assert isinstance(item, str)
        assert len(item) > 0


# ── SUG-11 ────────────────────────────────────────────────────────────────────

def test_sug_11_ev_commute_charging_suggestion_present():
    """SUG-11: electric_vehicle commute → EV off-peak charging suggestion."""
    profile = _profile(commute_mode="electric_vehicle", avg_daily_km=20.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_EV_OFFPEAK in result


def test_sug_11_ev_suggestion_contains_offpeak_hours():
    """SUG-11 (content): EV suggestion mentions off-peak hours."""
    profile = _profile(commute_mode="electric_vehicle", avg_daily_km=5.0)
    result = get_rule_based_suggestions(profile)
    ev_suggestions = [s for s in result if "off-peak" in s.lower() or "10pm" in s]
    assert len(ev_suggestions) >= 1


# ── SUG-12 ────────────────────────────────────────────────────────────────────

def test_sug_12_persona_passed_to_gemini_prompt(monkeypatch):
    """SUG-12: persona string appears in the prompt sent to AI."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["tip one", "tip two", "tip three"]
    persona = "teenager"
    captured_prompts: list[str] = []

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        def capture(prompt):
            captured_prompts.append(prompt)
            return json.dumps(original)

        mock_generate.side_effect = capture
        polish_suggestions(original, persona)

    assert len(captured_prompts) == 1
    assert persona in captured_prompts[0]


def test_sug_12_each_persona_produces_different_prompt(monkeypatch):
    """SUG-12 (variant): each persona produces a distinct prompt string."""
    original = ["a", "b", "c"]
    personas = ["student", "professional", "family", "teenager", "senior"]
    prompts: list[str] = []

    for persona in personas:
        from utils.suggestion_engine import _build_polish_prompt
        prompts.append(_build_polish_prompt(original, persona))

    # All prompts must be distinct
    assert len(set(prompts)) == len(personas), (
        "Each persona should produce a unique prompt"
    )
    # Each prompt must contain its persona name
    for persona, prompt in zip(personas, prompts):
        assert persona in prompt


# ── Additional robustness tests ───────────────────────────────────────────────

def test_non_dict_profile_raises_suggestion_error():
    """get_rule_based_suggestions raises SuggestionError for non-dict input."""
    with pytest.raises(SuggestionError):
        get_rule_based_suggestions(["not", "a", "dict"])  # type: ignore[arg-type]


def test_two_wheeler_over_5km_suggestion_present():
    """petrol_two_wheeler > 5km → two-wheeler suggestion present."""
    profile = _profile(commute_mode="petrol_two_wheeler", avg_daily_km=6.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_TWO_WHEELER_HIGH_KM in result


def test_two_wheeler_exactly_5km_no_suggestion():
    """petrol_two_wheeler = 5.0km → rule does NOT fire (> not >=)."""
    profile = _profile(commute_mode="petrol_two_wheeler", avg_daily_km=5.0)
    result = get_rule_based_suggestions(profile)
    assert _SUG_TWO_WHEELER_HIGH_KM not in result


def test_rule_results_are_unique():
    """No duplicate strings in the suggestion list for typical profiles."""
    profile = _profile(commute_mode="petrol_car", avg_daily_km=20.0,
                       diet_type="non_vegetarian", ac_hours_per_day=8.0,
                       lpg_cylinders_per_month=2.0)
    result = get_rule_based_suggestions(profile)
    assert len(result) == len(set(result)), "Suggestions must not contain duplicates"


def test_polish_no_api_key_returns_original(monkeypatch):
    """polish_suggestions returns original list when OPENROUTER_API_KEY is not set."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    original = ["tip one", "tip two", "tip three"]
    result = polish_suggestions(original, "student")
    assert result == original


def test_polish_valid_response_returns_polished_list(monkeypatch):
    """polish_suggestions returns polished list when AI succeeds."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["raw tip one", "raw tip two", "raw tip three"]
    polished = ["polished tip one", "polished tip two", "polished tip three"]

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.return_value = json.dumps(polished)
        result = polish_suggestions(original, "family")

    assert result == polished


def test_gemini_called_exactly_once_for_polish(monkeypatch):
    """polish_suggestions makes exactly 1 AI call — never more."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original = ["a", "b", "c"]

    with patch("utils.suggestion_engine.generate_content") as mock_generate:
        mock_generate.return_value = json.dumps(original)
        polish_suggestions(original, "professional")
        assert mock_generate.call_count == 1
