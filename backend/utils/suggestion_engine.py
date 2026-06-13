"""Generates up to 3 personalised, persona-aware habit improvement suggestions per user.

Pipeline:
  1. get_rule_based_suggestions() — pure function, no API calls, evaluates profile rules.
  2. polish_suggestions()        — single Gemini call to adapt tone to user persona.
  3. get_suggestions()           — orchestrates both; degrades to unpolished on Gemini failure.

EFFICIENCY.md: Suggestion refresh = max 1 Gemini call. Rules always run first.
On any Gemini failure, the original rule-based strings are returned unchanged.
"""

# Standard library
import json
import os
import re

# Third-party
import google.generativeai as genai


# ── Custom exception ──────────────────────────────────────────────────────────

class SuggestionError(Exception):
    """Raised when suggestion rule generation fails due to a missing or invalid profile."""
    pass


# ── Constants ─────────────────────────────────────────────────────────────────

_MAX_SUGGESTIONS: int = 3
_GEMINI_MODEL: str = "gemini-1.5-flash"
_POLISH_MAX_WORDS: int = 30

# Thresholds — named so they are never magic numbers in rule bodies
_HIGH_AC_THRESHOLD: float = 6.0
_MODERATE_AC_THRESHOLD: float = 3.0
_HIGH_LPG_THRESHOLD: float = 1.0
_CAR_KM_THRESHOLD: float = 10.0
_TWO_WHEELER_KM_THRESHOLD: float = 5.0
_ZERO_AC: float = 0.0

_CAR_MODES: frozenset[str] = frozenset({"petrol_car", "diesel_car"})
_VALID_PERSONAS: frozenset[str] = frozenset({
    "student", "professional", "family", "teenager", "senior",
})

# ── Suggestion text constants — never inline magic strings in logic ───────────

_SUG_CAR_HIGH_KM = (
    "Consider switching to metro or bus for your daily commute — "
    "it could cut your transport emissions significantly."
)
_SUG_TWO_WHEELER_HIGH_KM = (
    "Even switching 2–3 days a week to public transport "
    "can make a real difference for two-wheeler commuters."
)
_SUG_EV_OFFPEAK = (
    "Great choice on the EV! Make sure you charge during "
    "off-peak hours (10pm–6am) to use cleaner grid power."
)
_SUG_DIET_NON_VEG = (
    "Replacing one non-veg meal per week with a "
    "plant-based option saves roughly 0.7 kg CO2."
)
_SUG_DIET_EGGETARIAN = (
    "Your diet is already lower-impact — try one "
    "fully plant-based day per week."
)
_SUG_AC_HIGH = (
    "Your AC usage is high. Setting it to 24°C instead "
    "of 18°C can cut electricity emissions by up to 30%."
)
_SUG_AC_MODERATE = (
    "Try using a fan alongside AC and set the thermostat "
    "to 24°C — comfort without the carbon."
)
_SUG_NO_AC = (
    "No AC usage — great! Ceiling fans use 95% less "
    "energy than AC."
)
_SUG_LPG_HIGH = (
    "High LPG usage detected. Consider an induction "
    "cooktop for daily cooking — it's cleaner and faster."
)
_SUG_FALLBACK = (
    "Track your habits daily — even small changes "
    "compound over a month."
)


# ── Rule helpers ──────────────────────────────────────────────────────────────

def _transport_suggestion(profile: dict) -> str | None:
    """Return the first matching transport suggestion or None.

    Args:
        profile: User profile dict.

    Returns:
        Suggestion string if a transport rule matches, else None.
    """
    mode = profile.get("commute_mode", "")
    km = float(profile.get("avg_daily_km", 0))

    if mode in _CAR_MODES and km > _CAR_KM_THRESHOLD:
        return _SUG_CAR_HIGH_KM
    if mode == "petrol_two_wheeler" and km > _TWO_WHEELER_KM_THRESHOLD:
        return _SUG_TWO_WHEELER_HIGH_KM
    if mode == "electric_vehicle":
        return _SUG_EV_OFFPEAK
    return None


def _diet_suggestion(profile: dict) -> str | None:
    """Return the first matching diet suggestion or None.

    Args:
        profile: User profile dict.

    Returns:
        Suggestion string if a diet rule matches, else None.
    """
    diet = profile.get("diet_type", "")
    if diet == "non_vegetarian":
        return _SUG_DIET_NON_VEG
    if diet == "eggetarian":
        return _SUG_DIET_EGGETARIAN
    return None


def _electricity_suggestion(profile: dict) -> str | None:
    """Return the first matching electricity/AC suggestion or None.

    Args:
        profile: User profile dict.

    Returns:
        Suggestion string if an AC rule matches, else None.
    """
    ac_hours = float(profile.get("ac_hours_per_day", 0))
    if ac_hours > _HIGH_AC_THRESHOLD:
        return _SUG_AC_HIGH
    if ac_hours > _MODERATE_AC_THRESHOLD:
        return _SUG_AC_MODERATE
    if ac_hours == _ZERO_AC:
        return _SUG_NO_AC
    return None


def _lpg_suggestion(profile: dict) -> str | None:
    """Return the LPG suggestion if usage exceeds the threshold, else None.

    Args:
        profile: User profile dict.

    Returns:
        Suggestion string if an LPG rule matches, else None.
    """
    lpg = float(profile.get("lpg_cylinders_per_month", 0))
    if lpg > _HIGH_LPG_THRESHOLD:
        return _SUG_LPG_HIGH
    return None


# ── Core functions ────────────────────────────────────────────────────────────

def get_rule_based_suggestions(profile: dict) -> list[str]:
    """Generate up to 3 habit improvement suggestions using rule-based logic.

    Pure function — no API calls, no DB access, no side effects.
    Rules are evaluated in order: transport → diet → electricity → LPG.
    The general fallback is appended whenever the list is still under 3.

    Args:
        profile: User profile dict with keys: commute_mode, avg_daily_km,
                 diet_type, ac_hours_per_day, lpg_cylinders_per_month.

    Returns:
        Exactly 3 suggestion strings.

    Raises:
        SuggestionError: If the profile is not a dict or is structurally invalid.
    """
    try:
        if not isinstance(profile, dict):
            raise SuggestionError(
                f"profile must be a dict, got {type(profile).__name__}"
            )

        suggestions: list[str] = []

        rule_fns = [
            _transport_suggestion,
            _diet_suggestion,
            _electricity_suggestion,
            _lpg_suggestion,
        ]

        for rule_fn in rule_fns:
            if len(suggestions) >= _MAX_SUGGESTIONS:
                break
            result = rule_fn(profile)
            if result is not None:
                suggestions.append(result)

        # Pad to exactly 3 with the fallback
        while len(suggestions) < _MAX_SUGGESTIONS:
            suggestions.append(_SUG_FALLBACK)

        return suggestions[:_MAX_SUGGESTIONS]

    except SuggestionError:
        raise
    except Exception as e:
        raise SuggestionError(f"Rule-based suggestion generation failed: {e}") from e


def _build_polish_prompt(suggestions: list[str], persona: str) -> str:
    """Build the Gemini prompt for persona-aware suggestion polishing.

    Args:
        suggestions: List of rule-based suggestion strings.
        persona:     User persona string (student, professional, etc.).

    Returns:
        Prompt string ready to send to the Gemini API.
    """
    safe_persona = persona if persona in _VALID_PERSONAS else "professional"
    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(suggestions))
    return (
        f"Rewrite each of the following {_MAX_SUGGESTIONS} sustainability suggestions "
        f"for a {safe_persona} audience in India. "
        f"Keep each suggestion under {_POLISH_MAX_WORDS} words. "
        f"Do not change the core advice — only adapt the tone and language. "
        f"Return ONLY a JSON array of exactly {_MAX_SUGGESTIONS} strings. "
        f"No markdown. No explanation. No code fences.\n\n"
        f"Suggestions:\n{numbered}"
    )


def _parse_polish_response(raw: str) -> list[str] | None:
    """Parse a Gemini polish response into a list of strings.

    Strips markdown fences before attempting json.loads().

    Args:
        raw: Raw text from the Gemini API.

    Returns:
        List of suggestion strings if parse succeeds, else None.
    """
    try:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        result = json.loads(cleaned)
        if (
            isinstance(result, list)
            and len(result) == _MAX_SUGGESTIONS
            and all(isinstance(s, str) for s in result)
        ):
            return result
        return None
    except (json.JSONDecodeError, Exception):
        return None


def polish_suggestions(suggestions: list[str], persona: str) -> list[str]:
    """Polish rule-based suggestions with a single Gemini call for persona-aware tone.

    Sends one prompt to Gemini requesting a JSON array of rewritten suggestions.
    On any failure — API error, parse error, wrong response shape — the original
    suggestions are returned unchanged. This function never raises.

    Args:
        suggestions: List of rule-based suggestion strings (exactly 3).
        persona:     User persona string (student, professional, family, teenager, senior).

    Returns:
        List of 3 polished suggestion strings, or the original list on any failure.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return suggestions

        prompt = _build_polish_prompt(suggestions, persona)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_GEMINI_MODEL)
        response = model.generate_content(prompt)
        parsed = _parse_polish_response(response.text)
        return parsed if parsed is not None else suggestions

    except Exception:
        # Degrade gracefully — always return the original suggestions
        return suggestions


def get_suggestions(profile: dict, persona: str = "general") -> list[str]:
    """Orchestrate rule generation and Gemini polish to return 3 personalised suggestions.

    Steps:
      1. get_rule_based_suggestions(profile) — pure math/rules, always succeeds.
      2. polish_suggestions(rules, persona)  — single Gemini call, degrades on failure.

    Args:
        profile: User profile dict.
        persona: User persona string. Defaults to "general" (treated as professional).

    Returns:
        Exactly 3 suggestion strings (polished if Gemini succeeded, raw if not).

    Raises:
        SuggestionError: Only if rule generation itself fails (bad profile input).
    """
    try:
        raw_suggestions = get_rule_based_suggestions(profile)
        return polish_suggestions(raw_suggestions, persona)
    except SuggestionError:
        raise
    except Exception as e:
        raise SuggestionError(f"get_suggestions failed unexpectedly: {e}") from e
