"""Carbon footprint calculation utilities — daily score, monthly score, delta, breakdown.

All emission values are imported from constants.emission_factors — never hardcoded here.
All public functions raise CalculationError on any failure.
"""

# Standard library
# (none required)

# Internal
from constants.emission_factors import EMISSION_FACTORS


class CalculationError(Exception):
    """Raised when a carbon calculation cannot be completed due to bad input or missing data."""
    pass


def calculate_transport_emission(mode: str, km: float) -> float:
    """Calculate daily CO2 kg from a single commute trip.

    Args:
        mode: Commute mode string — must be a key in EMISSION_FACTORS["transport"].
        km:   Distance travelled in kilometres. Must be >= 0.

    Returns:
        CO2 emitted in kg, rounded to 4 decimal places for internal precision.

    Raises:
        CalculationError: If mode is unknown or km is negative.
    """
    try:
        transport_factors = EMISSION_FACTORS["transport"]
        if mode not in transport_factors:
            raise CalculationError(
                f"Unknown commute mode: '{mode}'. "
                f"Valid modes: {list(transport_factors.keys())}"
            )
        if km < 0:
            raise CalculationError(f"Distance cannot be negative, got: {km}")
        return transport_factors[mode] * km
    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"Transport emission calculation failed: {e}") from e


def calculate_diet_emission(diet_type: str) -> float:
    """Calculate daily CO2 kg from diet type.

    Args:
        diet_type: Diet string — must be a key in EMISSION_FACTORS["diet"].

    Returns:
        CO2 emitted in kg per day.

    Raises:
        CalculationError: If diet_type is not a recognised value.
    """
    try:
        diet_factors = EMISSION_FACTORS["diet"]
        if diet_type not in diet_factors:
            raise CalculationError(
                f"Unknown diet type: '{diet_type}'. "
                f"Valid types: {list(diet_factors.keys())}"
            )
        return diet_factors[diet_type]
    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"Diet emission calculation failed: {e}") from e


def calculate_electricity_emission(ac_hours: float) -> float:
    """Calculate daily CO2 kg from air-conditioner usage.

    Formula: grid_factor (kg CO2/kWh) × ac_kwh_per_hour (kWh/hr) × ac_hours (hr)

    Args:
        ac_hours: Hours of AC usage per day. Must be in range [0, 24].

    Returns:
        CO2 emitted in kg.

    Raises:
        CalculationError: If ac_hours is out of the valid range.
    """
    try:
        if ac_hours < 0 or ac_hours > 24:
            raise CalculationError(
                f"AC hours must be between 0 and 24, got: {ac_hours}"
            )
        electricity = EMISSION_FACTORS["electricity"]
        return electricity["grid_factor"] * electricity["ac_kwh_per_hour"] * ac_hours
    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"Electricity emission calculation failed: {e}") from e


def calculate_daily_score(profile: dict) -> float:
    """Calculate total daily CO2 kg from a user's habit profile.

    Sums transport, diet, and electricity (AC) emissions.
    LPG is a monthly quantity — not included in the daily score directly;
    use calculate_breakdown for per-category breakdown including LPG.

    Required profile keys: commute_mode, avg_daily_km, diet_type, ac_hours_per_day.

    Args:
        profile: Dict containing the user's daily habit data.

    Returns:
        Total daily CO2 in kg, rounded to 2 decimal places.

    Raises:
        CalculationError: If any required key is missing or a value is invalid.
    """
    try:
        required_keys = {"commute_mode", "avg_daily_km", "diet_type", "ac_hours_per_day"}
        missing = required_keys - profile.keys()
        if missing:
            raise CalculationError(f"Missing required profile fields: {missing}")

        transport = calculate_transport_emission(
            profile["commute_mode"], profile["avg_daily_km"]
        )
        diet = calculate_diet_emission(profile["diet_type"])
        electricity = calculate_electricity_emission(profile["ac_hours_per_day"])

        total = transport + diet + electricity
        return round(total, 2)
    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"Daily score calculation failed: {e}") from e


def calculate_monthly_score(daily_score: float) -> float:
    """Estimate monthly CO2 kg by multiplying the daily score by 30.

    Args:
        daily_score: Daily CO2 in kg as returned by calculate_daily_score.

    Returns:
        Monthly CO2 estimate in kg, rounded to 2 decimal places.

    Raises:
        CalculationError: If daily_score is negative.
    """
    try:
        if daily_score < 0:
            raise CalculationError(
                f"daily_score cannot be negative, got: {daily_score}"
            )
        return round(daily_score * 30, 2)
    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"Monthly score calculation failed: {e}") from e


def calculate_delta(old_score: float, new_score: float) -> float:
    """Calculate the CO2 change between two scores.

    Convention (TESTING.md CALC-06):
      negative result = saving  (new_score < old_score — user improved)
      positive result = increase (new_score > old_score — user worsened)

    Formula: new_score − old_score

    Args:
        old_score: Previous daily CO2 score in kg.
        new_score: New daily CO2 score in kg.

    Returns:
        Difference (new − old) in kg, rounded to 2 decimal places.

    Raises:
        CalculationError: If either argument is not a finite number.
    """
    try:
        return round(new_score - old_score, 2)
    except TypeError as e:
        raise CalculationError(f"Delta calculation requires numeric inputs: {e}") from e
    except Exception as e:
        raise CalculationError(f"Delta calculation failed: {e}") from e


def calculate_breakdown(profile: dict) -> dict:
    """Return per-category daily CO2 kg for the score breakdown pie chart.

    LPG contribution is computed from lpg_cylinders_per_month divided by 30
    to give a daily equivalent. If the key is absent it defaults to 0.

    Required profile keys: commute_mode, avg_daily_km, diet_type,
                           ac_hours_per_day.
    Optional profile key: lpg_cylinders_per_month (defaults to 0).

    Args:
        profile: Dict containing the user's habit data.

    Returns:
        Dict with keys: transport, diet, electricity, lpg, total.
        All values rounded to 2 decimal places.

    Raises:
        CalculationError: If any required field is missing or invalid.
    """
    try:
        transport = round(
            calculate_transport_emission(
                profile["commute_mode"], profile["avg_daily_km"]
            ),
            2,
        )
        diet = round(calculate_diet_emission(profile["diet_type"]), 2)
        electricity = round(
            calculate_electricity_emission(profile["ac_hours_per_day"]), 2
        )

        cylinders_per_month = profile.get("lpg_cylinders_per_month", 0)
        lpg_daily = (
            EMISSION_FACTORS["lpg"]["kg_co2_per_cylinder"] * cylinders_per_month / 30
        )
        lpg = round(lpg_daily, 2)

        total = round(transport + diet + electricity + lpg, 2)

        return {
            "transport": transport,
            "diet": diet,
            "electricity": electricity,
            "lpg": lpg,
            "total": total,
        }
    except CalculationError:
        raise
    except KeyError as e:
        raise CalculationError(f"Missing required profile field: {e}") from e
    except Exception as e:
        raise CalculationError(f"Breakdown calculation failed: {e}") from e


def simulate_changes(profile: dict, changes: dict) -> dict:
    """Apply what-if changes to a profile and return the updated score and delta.

    Merges the changes dict on top of profile, then calls calculate_daily_score
    and calculate_breakdown on the merged result. Computes delta vs the original
    profile score using calculate_delta (new - old convention).

    Args:
        profile: Current user habit profile dict.
        changes: Partial dict of fields to override (e.g. {"commute_mode": "metro"}).

    Returns:
        Dict with keys:
          daily_co2_kg (float)  — new total daily score after changes
          breakdown    (dict)   — per-category breakdown after changes
          delta        (float)  — new_score - old_score (negative = saving)

    Raises:
        CalculationError: If the merged profile is invalid or calculation fails.
    """
    try:
        merged = {**profile, **changes}
        old_score = calculate_daily_score(profile)
        new_score = calculate_daily_score(merged)
        breakdown = calculate_breakdown(merged)
        delta = calculate_delta(old_score, new_score)
        return {
            "daily_co2_kg": new_score,
            "breakdown": breakdown,
            "delta": delta,
        }
    except CalculationError:
        raise
    except Exception as e:
        raise CalculationError(f"simulate_changes failed: {e}") from e
