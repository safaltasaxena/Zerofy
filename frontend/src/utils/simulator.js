/**
 * simulator.js — Pure frontend math for what-if carbon calculations.
 *
 * EFFICIENCY.md §3: Simulator math runs entirely in the browser.
 * No API calls, no await, no async. Uses constants loaded once on app start.
 *
 * CODING_STANDARDS.md §1.7 / §2.5:
 * No hardcoded emission numbers — all values come from getConstants().
 *
 * Mirrors the backend calculate_daily_score() + calculate_breakdown() logic exactly.
 */

import { getConstants } from './constants'

// ── Internal calculation helpers ──────────────────────────────────────────────

/**
 * Calculate transport CO2 in kg for a given mode and distance.
 *
 * @param {string} commuteMode - Transport mode key (e.g. "metro", "petrol_car")
 * @param {number} avgDailyKm  - Daily commute distance in km
 * @param {Object} transport   - Transport section of the constants object
 * @returns {number} Transport CO2 in kg
 * @throws {Error} If the commute mode is not found in constants
 */
function _calcTransport(commuteMode, avgDailyKm, transport) {
  const factor = transport[commuteMode]
  if (factor === undefined) {
    throw new Error(`Unknown commute_mode: "${commuteMode}"`)
  }
  return factor * avgDailyKm
}

/**
 * Calculate diet CO2 in kg per day.
 *
 * @param {string} dietType - Diet type key (e.g. "vegetarian", "vegan")
 * @param {Object} diet     - Diet section of the constants object
 * @returns {number} Diet CO2 in kg
 * @throws {Error} If the diet type is not found in constants
 */
function _calcDiet(dietType, diet) {
  const factor = diet[dietType]
  if (factor === undefined) {
    throw new Error(`Unknown diet_type: "${dietType}"`)
  }
  return factor
}

/**
 * Calculate electricity (AC) CO2 in kg per day.
 *
 * @param {number} acHoursPerDay - Hours of AC use per day
 * @param {Object} electricity   - Electricity section of the constants object
 * @returns {number} Electricity CO2 in kg
 */
function _calcElectricity(acHoursPerDay, electricity) {
  return electricity.grid_factor * electricity.ac_kwh_per_hour * acHoursPerDay
}

/**
 * Calculate LPG CO2 in kg per day (monthly cylinders → daily).
 *
 * @param {number} cylindersPerMonth - LPG cylinders used per month
 * @param {Object} lpg               - LPG section of the constants object
 * @returns {number} LPG CO2 in kg per day
 */
function _calcLpg(cylindersPerMonth, lpg) {
  return (lpg.kg_co2_per_cylinder * cylindersPerMonth) / 30
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Calculate daily CO2 score and category breakdown for a what-if habit profile.
 *
 * Mirrors backend calculate_daily_score() + calculate_breakdown() exactly.
 * Synchronous — no async, no await, no API calls.
 * Uses constants loaded from /api/constants via loadConstants().
 *
 * @param {Object} params
 * @param {string} params.commute_mode            - Transport mode key
 * @param {number} params.avg_daily_km            - Daily commute distance in km
 * @param {string} params.diet_type               - Diet type key
 * @param {number} params.ac_hours_per_day        - AC hours per day
 * @param {number} params.lpg_cylinders_per_month - LPG cylinders per month
 * @returns {{ daily_co2_kg: number, breakdown: Object }}
 * @throws {Error} If constants are not loaded or a param key is unknown
 */
export function simulate(params) {
  try {
    const { commute_mode, avg_daily_km, diet_type, ac_hours_per_day, lpg_cylinders_per_month } = params
    const constants = getConstants()

    const transport   = _calcTransport(commute_mode, avg_daily_km, constants.transport)
    const diet        = _calcDiet(diet_type, constants.diet)
    const electricity = _calcElectricity(ac_hours_per_day, constants.electricity)
    const lpg        = _calcLpg(lpg_cylinders_per_month, constants.lpg)

    const total = transport + diet + electricity + lpg
    const daily_co2_kg = Math.round(total * 100) / 100

    return {
      daily_co2_kg,
      breakdown: {
        transport: Math.round(transport * 100) / 100,
        diet:      Math.round(diet * 100) / 100,
        electricity: Math.round(electricity * 100) / 100,
        lpg:       Math.round(lpg * 100) / 100,
        total:     daily_co2_kg,
      },
    }
  } catch (err) {
    throw new Error(`simulate() failed: ${err.message}`)
  }
}
