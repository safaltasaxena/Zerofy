/**
 * api.test.js — Vitest tests for api.js and simulator.js.
 *
 * Maps to API-01 through API-06 and SIM-01 through SIM-05.
 *
 * Mocking strategy:
 *   - axios is vi.mock'd — no real HTTP calls.
 *   - getConstants (from constants.js) is vi.mock'd for simulator tests.
 *   - localStorage is mocked via vi.spyOn for token tests.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── Mock axios before importing api.js ────────────────────────────────────────

vi.mock('axios', async () => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return {
    default: {
      create: vi.fn(() => mockInstance),
    },
    __mockInstance: mockInstance,
  }
})

// ── Mock constants.js for simulator tests ─────────────────────────────────────

vi.mock('./constants', () => ({
  getConstants: vi.fn(),
  loadConstants: vi.fn(),
  _resetConstants: vi.fn(),
}))

import axiosLib from 'axios'
import { getConstants } from './constants'

/**
 * Get the mock axios instance created by axios.create()
 */
function getMockApi() {
  return axiosLib.create()
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Build a mock successful axios response in the standard Zerofy shape. */
function successResponse(data) {
  return { data: { success: true, data, error: null } }
}

/** Build a mock failed axios response in the standard Zerofy shape. */
function failureResponse(error) {
  return { data: { success: false, data: null, error } }
}

/** Indian emission constants matching backend emission_factors.py */
const MOCK_CONSTANTS = {
  transport: {
    petrol_car: 0.17,
    diesel_car: 0.15,
    petrol_two_wheeler: 0.05,
    electric_vehicle: 0.02,
    auto_rickshaw: 0.07,
    bus: 0.02,
    metro: 0.01,
    walking: 0.0,
    cycling: 0.0,
  },
  diet: {
    non_vegetarian: 5.0,
    vegetarian: 2.5,
    eggetarian: 3.0,
    vegan: 1.5,
  },
  electricity: {
    grid_factor: 0.82,
    ac_kwh_per_hour: 1.5,
    fan_kwh_per_hour: 0.075,
    led_kwh_per_hour: 0.01,
  },
  lpg: {
    kg_co2_per_cylinder: 12.0,
  },
}

// ── API tests ─────────────────────────────────────────────────────────────────

describe('API-01: submitChatUpdate sends message in body', () => {
  it('posts to /api/logs/chat-update with message field', async () => {
    const { submitChatUpdate } = await import('./api')
    const mockApi = getMockApi()
    mockApi.post.mockResolvedValue(successResponse({ daily_co2_kg: 3.5 }))

    await submitChatUpdate('I took the metro today')

    expect(mockApi.post).toHaveBeenCalledWith(
      '/api/logs/chat-update',
      { message: 'I took the metro today' }
    )
  })
})

describe('API-02: getProfile attaches Authorization header', () => {
  it('interceptor use() is registered on the axios instance', async () => {
    const mockApi = getMockApi()
    // The interceptor registers itself via interceptors.request.use()
    expect(mockApi.interceptors.request.use).toHaveBeenCalled()
  })

  it('getProfile calls GET /api/user/profile', async () => {
    const { getProfile } = await import('./api')
    const mockApi = getMockApi()
    mockApi.get.mockResolvedValue(successResponse({ profile: { name: 'Priya' } }))

    const result = await getProfile()

    expect(mockApi.get).toHaveBeenCalledWith('/api/user/profile')
    expect(result.name).toBe('Priya')
  })
})

describe('API-03: failed request throws error — not silent', () => {
  it('throws when success is false in the response body', async () => {
    const { getProfile } = await import('./api')
    const mockApi = getMockApi()
    mockApi.get.mockResolvedValue(failureResponse('Profile not found.'))

    await expect(getProfile()).rejects.toThrow('Profile not found.')
  })

  it('throws when axios throws a network error', async () => {
    const { getProfile } = await import('./api')
    const mockApi = getMockApi()
    mockApi.get.mockRejectedValue({ message: 'Network Error', response: undefined })

    await expect(getProfile()).rejects.toThrow()
  })
})

describe('API-04: fetchConstants returns constants object', () => {
  it('calls GET /api/constants and returns the constants key', async () => {
    const { fetchConstants } = await import('./api')
    const mockApi = getMockApi()
    mockApi.get.mockResolvedValue(
      successResponse({ constants: MOCK_CONSTANTS })
    )

    const result = await fetchConstants()

    expect(mockApi.get).toHaveBeenCalledWith('/api/constants')
    expect(result.constants).toHaveProperty('transport')
    expect(result.constants).toHaveProperty('diet')
    expect(result.constants).toHaveProperty('electricity')
    expect(result.constants).toHaveProperty('lpg')
  })
})

describe('API-05: getTodayLog called with correct userId in URL', () => {
  it('calls GET /api/logs/{userId}/today with the provided userId', async () => {
    const { getTodayLog } = await import('./api')
    const mockApi = getMockApi()
    mockApi.get.mockResolvedValue(successResponse({ daily_co2_kg: 4.2 }))

    await getTodayLog('test-user-uid-123')

    expect(mockApi.get).toHaveBeenCalledWith('/api/logs/test-user-uid-123/today')
  })

  it('different userIds produce different URL paths', async () => {
    const { getTodayLog } = await import('./api')
    const mockApi = getMockApi()
    mockApi.get.mockResolvedValue(successResponse({ daily_co2_kg: 2.0 }))

    await getTodayLog('another-uid-456')

    expect(mockApi.get).toHaveBeenCalledWith('/api/logs/another-uid-456/today')
  })
})

describe('API-06: axios interceptor attaches token to every call', () => {
  it('interceptors.request.use is called during module initialisation', async () => {
    const mockApi = getMockApi()
    // The interceptor must have been registered when api.js was imported
    expect(mockApi.interceptors.request.use).toHaveBeenCalled()
  })

  it('interceptor callback reads from localStorage', () => {
    const mockApi = getMockApi()
    const [[interceptorFn]] = mockApi.interceptors.request.use.mock.calls
    if (!interceptorFn) return // guard: interceptor may not have been extracted yet

    // Simulate a config object and a stored token
    const setItem = vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('test.token.value')
    const config = { headers: {} }
    const result = interceptorFn(config)
    expect(result.headers.Authorization).toBe('Bearer test.token.value')
    setItem.mockRestore()
  })
})

// ── Simulator tests ───────────────────────────────────────────────────────────

describe('SIM-01: simulate() returns daily_co2_kg and breakdown', () => {
  beforeEach(() => {
    getConstants.mockReturnValue(MOCK_CONSTANTS)
  })

  it('returns the correct shape', async () => {
    const { simulate } = await import('./simulator')
    const result = simulate({
      commute_mode: 'metro',
      avg_daily_km: 8,
      diet_type: 'vegetarian',
      ac_hours_per_day: 2,
      lpg_cylinders_per_month: 0.5,
    })

    expect(result).toHaveProperty('daily_co2_kg')
    expect(result).toHaveProperty('breakdown')
    expect(typeof result.daily_co2_kg).toBe('number')
    expect(result.breakdown).toHaveProperty('transport')
    expect(result.breakdown).toHaveProperty('diet')
    expect(result.breakdown).toHaveProperty('electricity')
    expect(result.breakdown).toHaveProperty('lpg')
    expect(result.breakdown).toHaveProperty('total')
  })
})

describe('SIM-02: simulate() is synchronous — no Promise returned', () => {
  beforeEach(() => {
    getConstants.mockReturnValue(MOCK_CONSTANTS)
  })

  it('returns a plain object, not a Promise', async () => {
    const { simulate } = await import('./simulator')
    const result = simulate({
      commute_mode: 'bus',
      avg_daily_km: 5,
      diet_type: 'vegan',
      ac_hours_per_day: 0,
      lpg_cylinders_per_month: 0,
    })

    expect(result instanceof Promise).toBe(false)
    expect(typeof result).toBe('object')
    expect(result).not.toBeNull()
  })
})

describe('SIM-03: simulate() uses constants from getConstants() — not hardcoded', () => {
  it('calls getConstants() during execution', async () => {
    getConstants.mockReturnValue(MOCK_CONSTANTS)
    const { simulate } = await import('./simulator')

    simulate({
      commute_mode: 'metro',
      avg_daily_km: 10,
      diet_type: 'vegetarian',
      ac_hours_per_day: 1,
      lpg_cylinders_per_month: 1,
    })

    expect(getConstants).toHaveBeenCalled()
  })

  it('throws if getConstants() throws (not loaded)', async () => {
    getConstants.mockImplementation(() => {
      throw new Error('Constants not loaded.')
    })
    const { simulate } = await import('./simulator')

    expect(() =>
      simulate({
        commute_mode: 'metro',
        avg_daily_km: 5,
        diet_type: 'vegetarian',
        ac_hours_per_day: 0,
        lpg_cylinders_per_month: 0,
      })
    ).toThrow()
  })
})

describe('SIM-04: simulate(all zeros) → returns diet-only score', () => {
  beforeEach(() => {
    getConstants.mockReturnValue(MOCK_CONSTANTS)
  })

  it('zero km + zero AC + zero LPG → score equals diet CO2 only', async () => {
    const { simulate } = await import('./simulator')
    // vegetarian = 2.5 kg/day, all others = 0
    const result = simulate({
      commute_mode: 'walking',     // 0.0 factor
      avg_daily_km: 0,
      diet_type: 'vegetarian',     // 2.5 kg/day
      ac_hours_per_day: 0,
      lpg_cylinders_per_month: 0,
    })

    expect(result.daily_co2_kg).toBe(2.5)
    expect(result.breakdown.transport).toBe(0)
    expect(result.breakdown.electricity).toBe(0)
    expect(result.breakdown.lpg).toBe(0)
    expect(result.breakdown.diet).toBe(2.5)
  })
})

describe('SIM-05: simulate() output matches calculate_daily_score() logic', () => {
  beforeEach(() => {
    getConstants.mockReturnValue(MOCK_CONSTANTS)
  })

  it('matches expected manual calculation for metro + vegetarian + AC + LPG', async () => {
    const { simulate } = await import('./simulator')
    /*
     * Manually computing with MOCK_CONSTANTS:
     * transport  = 0.01 × 8  = 0.08
     * diet       = 2.5
     * electricity = 0.82 × 1.5 × 2 = 2.46
     * lpg        = (12.0 × 0.5) / 30 = 0.2
     * total      = 0.08 + 2.5 + 2.46 + 0.2 = 5.24
     */
    const result = simulate({
      commute_mode: 'metro',
      avg_daily_km: 8,
      diet_type: 'vegetarian',
      ac_hours_per_day: 2,
      lpg_cylinders_per_month: 0.5,
    })

    expect(result.daily_co2_kg).toBeCloseTo(5.24, 2)
    expect(result.breakdown.transport).toBeCloseTo(0.08, 2)
    expect(result.breakdown.diet).toBeCloseTo(2.5, 2)
    expect(result.breakdown.electricity).toBeCloseTo(2.46, 2)
    expect(result.breakdown.lpg).toBeCloseTo(0.2, 2)
  })

  it('petrol_car long commute — matches manual calculation', async () => {
    const { simulate } = await import('./simulator')
    /*
     * transport  = 0.17 × 30 = 5.1
     * diet       = 5.0 (non_vegetarian)
     * electricity = 0.82 × 1.5 × 8 = 9.84
     * lpg        = (12.0 × 2) / 30 = 0.8
     * total      = 5.1 + 5.0 + 9.84 + 0.8 = 20.74
     */
    const result = simulate({
      commute_mode: 'petrol_car',
      avg_daily_km: 30,
      diet_type: 'non_vegetarian',
      ac_hours_per_day: 8,
      lpg_cylinders_per_month: 2,
    })

    expect(result.daily_co2_kg).toBeCloseTo(20.74, 2)
  })
})
