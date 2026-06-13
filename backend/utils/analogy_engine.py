"""Converts raw CO2 kg values into human-readable, India-relevant analogy strings.

Pure function module — no DB calls, no API calls, no external imports beyond math.
All analogy text is hardcoded here (UI strings, not emission factors).
"""

# Standard library
import math

# Internal
from utils.calculator import CalculationError


# ── Analogy lookup table ────────────────────────────────────────────────────
# Each entry: (upper_bound_inclusive, scale_factor, template)
# {n} in template is replaced with round(co2_kg * scale_factor, 1)
# upper_bound = math.inf for the open-ended top bracket.
_GENERAL_ANALOGIES: list[tuple[float, float, str]] = [
    # 0.01–1.0 kg → smartphone charges  (1 kg = 121 charges)
    (1.0,       121.0,  "Like charging {n} smartphones 🔋 "
                        "(1 kg CO₂ = 121 smartphone charges)"),
    # 1.01–3.0 kg → ceiling fan hours  (1 kg = 20 hours)
    (3.0,       20.0,   "Like running a ceiling fan for {n} hours 🌀 "
                        "(1 kg CO₂ = 20 ceiling fan hours)"),
    # 3.01–6.0 kg → hours of TV  (1 kg = 7 hours)
    (6.0,       7.0,    "Like watching {n} hours of TV 📺 "
                        "(1 kg CO₂ = 7 hours of TV)"),
    # 6.01–10.0 kg → kettle boils  (1 kg = 14 boils)
    (10.0,      14.0,   "Like boiling {n} kettles of water ☕ "
                        "(1 kg CO₂ = 14 kettle boils)"),
    # Above 10.0 kg → km in petrol car  (1 kg = 5.9 km)
    (math.inf,  5.9,    "Like driving {n} km in a petrol car 🚗 "
                        "(1 kg CO₂ = 5.9 km)"),
]

# Transport-specific analogies — keyed by rough range (upper bound)
_TRANSPORT_ANALOGIES: list[tuple[float, float, str]] = [
    (1.0,       20.0,   "Like riding a petrol two-wheeler for {n} km 🛵"),
    (3.0,       5.9,    "Like driving a petrol car for {n} km 🚗"),
    (6.0,       5.9,    "Like driving a petrol car for {n} km 🚗 — "
                        "consider metro or cycling for part of the trip"),
    (10.0,      5.9,    "Like driving a petrol car for {n} km 🚗 — "
                        "a long way! Carpooling or metro would help a lot"),
    (math.inf,  5.9,    "Like driving a petrol car for {n} km 🚗 — "
                        "that's a lot of road. Consider public transport 🚇"),
]

_ZERO_STATE_MESSAGE = "You had a zero-carbon day 🌱"


def _format_analogy(co2_kg: float, table: list[tuple[float, float, str]]) -> str:
    """Look up the analogy for co2_kg in the given table and format it.

    Args:
        co2_kg: Non-negative CO2 value in kg.
        table:  Sorted list of (upper_bound, scale_factor, template) tuples.

    Returns:
        Formatted analogy string with {n} replaced by the scaled value.
    """
    for upper_bound, scale_factor, template in table:
        if co2_kg <= upper_bound:
            scaled = round(co2_kg * scale_factor, 1)
            return template.replace("{n}", str(scaled))
    # Fallback — should never be reached if table ends with math.inf
    return f"Equivalent to {round(co2_kg, 2)} kg CO₂ emitted"


def get_analogy(co2_kg: float, context: str = "general") -> str:
    """Convert a CO2 kg value into a human-readable, India-relevant analogy string.

    Selects the appropriate analogy based on the magnitude of co2_kg and the
    context in which the CO2 was generated (transport, electricity, diet, general).

    Args:
        co2_kg:  CO2 emitted in kg. Must be >= 0.
        context: Usage context — "general" (default) or "transport".
                 Unknown contexts fall back to "general".

    Returns:
        A non-empty analogy string. Never returns None.

    Raises:
        CalculationError: If co2_kg is negative.
    """
    try:
        if not isinstance(co2_kg, (int, float)):
            raise CalculationError(
                f"co2_kg must be a number, got {type(co2_kg).__name__}"
            )
        if co2_kg < 0:
            raise CalculationError(
                f"co2_kg cannot be negative, got: {co2_kg}"
            )

        # Zero-emission day — special case regardless of context
        if co2_kg == 0.0:
            return _ZERO_STATE_MESSAGE

        if context == "transport":
            return _format_analogy(co2_kg, _TRANSPORT_ANALOGIES)

        # Default: "general" (and any unknown context)
        return _format_analogy(co2_kg, _GENERAL_ANALOGIES)

    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"Analogy lookup failed: {e}") from e
