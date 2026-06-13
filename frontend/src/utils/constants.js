/**
 * constants.js — Module-level constants store.
 *
 * Emission factors are fetched ONCE from /api/constants on app start
 * and stored here. All other modules read from this store synchronously.
 *
 * EFFICIENCY.md §1: No hardcoded emission numbers anywhere in frontend.
 * The only source of truth is backend/constants/emission_factors.py,
 * served via GET /api/constants and accessed here via fetchConstants().
 *
 * Usage:
 *   import { loadConstants, getConstants } from './constants'
 *   await loadConstants()          // call once on app start
 *   const c = getConstants()       // synchronous read everywhere else
 */

import { fetchConstants } from './api.js'

/** @type {Object|null} — populated by loadConstants(), null until then */
let _constants = null

/**
 * Fetch emission constants from the backend (via api.js) and store them.
 * Idempotent — returns immediately if constants are already loaded.
 * Must be called once before any call to getConstants().
 *
 * @returns {Promise<void>}
 * @throws {Error} If the fetch fails or the response is invalid.
 */
export async function loadConstants() {
  if (_constants) return
  _constants = await fetchConstants()
}

/**
 * Return the stored constants object synchronously.
 * Throws if loadConstants() has not been called yet.
 *
 * @returns {Object} The emission constants object.
 * @throws {Error} If the constants store has not been populated.
 */
export function getConstants() {
  if (_constants === null) {
    throw new Error(
      'Constants not loaded. Call loadConstants() on app start before using getConstants().'
    )
  }
  return _constants
}

/**
 * Reset the module-level store to null.
 * Intended for use in tests only — not for production code.
 */
export function _resetConstants() {
  _constants = null
}
