/**
 * Dashboard.test.jsx — Tests for Dashboard.jsx (DASH-01 through DASH-12).
 *
 * Child components are mocked to keep tests focused on Dashboard orchestration.
 * All API calls mocked via vi.mock — no real HTTP.
 * localStorage populated in beforeEach — userId never hardcoded in assertions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axe from 'axe-core'

// ── Mock child components (test Dashboard orchestration, not component internals) ──

vi.mock('../components/ScoreBreakdown', () => ({
  default: ({ breakdown, isLoading }) => {
    if (isLoading) return <div data-testid="score-loading">score-loading</div>
    const total = breakdown?.total ?? 0
    if (total === 0) return <div data-testid="score-empty">Zero emissions logged yet today</div>
    return <div data-testid="score-breakdown">breakdown-total-{total}</div>
  },
}))

vi.mock('../components/SuggestionsList', () => ({
  default: ({ suggestions, isLoading }) => {
    if (isLoading) return <div data-testid="sugg-loading">sugg-loading</div>
    return (
      <ul data-testid="suggestions-list">
        {(suggestions || []).map((s, i) => <li key={i}>{s}</li>)}
      </ul>
    )
  },
}))

vi.mock('../components/StreakCounter', () => ({
  default: ({ streak, isLoading }) => {
    if (isLoading) return <div data-testid="streak-loading">streak-loading</div>
    return <div data-testid="streak-counter">{streak} days</div>
  },
}))

vi.mock('../components/WeeklyChart', () => ({
  default: ({ trend, isLoading }) => {
    if (isLoading) return <div data-testid="chart-loading">chart-loading</div>
    return <div data-testid="weekly-chart">{(trend || []).length} entries</div>
  },
}))

vi.mock('../components/LeaderboardSnippet', () => ({
  default: ({ state, isLoading }) => {
    if (isLoading) return <div data-testid="lb-loading">lb-loading</div>
    return (
      <div data-testid="leaderboard-snippet">
        <div>1st</div>
        <div>2nd</div>
        <div>3rd</div>
        <div data-testid="lb-state">{state}</div>
      </div>
    )
  },
}))

// ── Mock api.js ───────────────────────────────────────────────────────────────

vi.mock('../utils/api', () => ({
  getProfile:     vi.fn(),
  getTodayLog:    vi.fn(),
  getGamification: vi.fn(),
  getWeeklyTrend: vi.fn(),
}))

import { getProfile, getTodayLog, getGamification, getWeeklyTrend } from '../utils/api'
import Dashboard from './Dashboard'

// ── Shared mock data ──────────────────────────────────────────────────────────

const MOCK_USER_ID = 'test-user-uid-777'

const MOCK_PROFILE = {
  name: 'Priya Sharma',
  state: 'Maharashtra',
  city: 'Mumbai',
  commute_mode: 'metro',
}

const MOCK_BREAKDOWN = {
  transport: 0.08, diet: 2.5, electricity: 1.46, lpg: 0.4, total: 4.44,
}

const MOCK_LOG = {
  breakdown: MOCK_BREAKDOWN,
  analogy: 'Like 540 smartphone charges 🔋',
  suggestions: [
    'Try metro tomorrow — saves ~0.8 kg CO2',
    'Switch to vegetarian dinner twice a week',
    'Set AC to 26°C instead of 22°C',
  ],
}

const MOCK_GAMIFICATION = {
  log_streak: 7, awareness_score: 120, badges: ['Early Bird'], weekly_score: 30,
}

const MOCK_TREND = {
  trend: [
    { date: '2026-06-07', daily_co2_kg: 4.2 },
    { date: '2026-06-08', daily_co2_kg: 3.8 },
    { date: '2026-06-09', daily_co2_kg: 5.1 },
    { date: '2026-06-10', daily_co2_kg: 4.5 },
    { date: '2026-06-11', daily_co2_kg: 3.9 },
    { date: '2026-06-12', daily_co2_kg: 4.0 },
    { date: '2026-06-13', daily_co2_kg: 4.44 },
  ],
}

// ── Setup / teardown ─────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.setItem('zerofy_user_id', MOCK_USER_ID)

  getProfile.mockResolvedValue(MOCK_PROFILE)
  getTodayLog.mockResolvedValue(MOCK_LOG)
  getGamification.mockResolvedValue(MOCK_GAMIFICATION)
  getWeeklyTrend.mockResolvedValue(MOCK_TREND)
})

afterEach(() => {
  localStorage.clear()
})

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  )
}

// ── DASH-01 ───────────────────────────────────────────────────────────────────

describe('DASH-01: Dashboard fetches profile, today log, and gamification in parallel on mount', () => {
  it('calls all 4 API functions on mount', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(getProfile).toHaveBeenCalledTimes(1)
      expect(getTodayLog).toHaveBeenCalledTimes(1)
      expect(getGamification).toHaveBeenCalledTimes(1)
      expect(getWeeklyTrend).toHaveBeenCalledTimes(1)
    })
  })

  it('passes userId from localStorage to getTodayLog and getGamification', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(getTodayLog).toHaveBeenCalledWith(MOCK_USER_ID)
      expect(getGamification).toHaveBeenCalledWith(MOCK_USER_ID)
    })
  })
})

// ── DASH-02 ───────────────────────────────────────────────────────────────────

describe('DASH-02: ScoreBreakdown renders with correct breakdown data', () => {
  it('shows breakdown total from todayLog', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('score-breakdown').textContent).toContain('4.44')
    })
  })
})

// ── DASH-03 ───────────────────────────────────────────────────────────────────

describe('DASH-03: SuggestionsList renders 3 suggestions', () => {
  it('renders all 3 suggestion strings', async () => {
    renderDashboard()
    await waitFor(() => {
      const list = screen.getByTestId('suggestions-list')
      expect(list.querySelectorAll('li').length).toBe(3)
    })
  })
})

// ── DASH-04 ───────────────────────────────────────────────────────────────────

describe('DASH-04: StreakCounter shows streak number', () => {
  it('shows the streak count from gamification', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('streak-counter').textContent).toContain('7')
    })
  })
})

// ── DASH-05 ───────────────────────────────────────────────────────────────────

describe('DASH-05: WeeklyChart renders with trend data', () => {
  it('receives trend entries from the weekly trend API', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('weekly-chart').textContent).toContain('7')
    })
  })
})

// ── DASH-06 ───────────────────────────────────────────────────────────────────

describe('DASH-06: LeaderboardSnippet renders top 3', () => {
  it('LeaderboardSnippet is present in the DOM', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('leaderboard-snippet')).not.toBeNull()
    })
  })

  it('renders rank labels 1st, 2nd, 3rd', async () => {
    renderDashboard()
    await waitFor(() => {
      const lb = screen.getByTestId('leaderboard-snippet')
      expect(lb.textContent).toContain('1st')
      expect(lb.textContent).toContain('2nd')
      expect(lb.textContent).toContain('3rd')
    })
  })

  it('passes user state to LeaderboardSnippet', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('lb-state').textContent).toBe('Maharashtra')
    })
  })
})

// ── DASH-07 ───────────────────────────────────────────────────────────────────

describe('DASH-07: Loading state shown before data arrives', () => {
  it('shows skeleton/loading states immediately on mount', async () => {
    // Make API calls hang — never resolve during this check
    getProfile.mockImplementation(() => new Promise(() => {}))
    getTodayLog.mockImplementation(() => new Promise(() => {}))
    getGamification.mockImplementation(() => new Promise(() => {}))
    getWeeklyTrend.mockImplementation(() => new Promise(() => {}))

    renderDashboard()

    expect(screen.getByTestId('score-loading')).not.toBeNull()
    expect(screen.getByTestId('sugg-loading')).not.toBeNull()
    expect(screen.getByTestId('streak-loading')).not.toBeNull()
    expect(screen.getByTestId('chart-loading')).not.toBeNull()
  })
})

// ── DASH-08 ───────────────────────────────────────────────────────────────────

describe('DASH-08: API error → error message shown, no crash', () => {
  it('displays a role=alert error message when getProfile rejects', async () => {
    getProfile.mockRejectedValue(new Error('Network error'))

    renderDashboard()

    await waitFor(() => {
      const alert = document.querySelector('[role="alert"]')
      expect(alert).not.toBeNull()
      expect(alert.textContent).toContain('Could not load')
    })
  })

  it('does not crash — component stays mounted after error', async () => {
    getProfile.mockRejectedValue(new Error('timeout'))
    const { container } = renderDashboard()
    await waitFor(() => {
      expect(container.firstChild).not.toBeNull()
    })
  })
})

// ── DASH-09 (EDGE-20) ─────────────────────────────────────────────────────────

describe('DASH-09: EDGE-20 — all-zero breakdown → empty state, no divide-by-zero crash', () => {
  it('renders empty state when all breakdown values are zero', async () => {
    getTodayLog.mockResolvedValue({
      breakdown: { transport: 0, diet: 0, electricity: 0, lpg: 0, total: 0 },
      analogy: '',
      suggestions: [],
    })

    renderDashboard()

    await waitFor(() => {
      expect(screen.getByTestId('score-empty')).not.toBeNull()
      expect(screen.getByTestId('score-empty').textContent).toContain('Zero emissions logged')
    })
  })

  it('does not throw when total is 0', async () => {
    getTodayLog.mockResolvedValue({
      breakdown: { transport: 0, diet: 0, electricity: 0, lpg: 0, total: 0 },
    })

    expect(() => renderDashboard()).not.toThrow()
    await waitFor(() => {
      expect(screen.getByTestId('score-empty')).not.toBeNull()
    })
  })
})

// ── DASH-10 (EDGE-23) ─────────────────────────────────────────────────────────

describe('DASH-10: EDGE-23 — double fetch blocked, Promise.all called only once per mount', () => {
  it('each API function is called exactly once per mount', async () => {
    renderDashboard()

    await waitFor(() => {
      expect(getProfile).toHaveBeenCalledTimes(1)
      expect(getTodayLog).toHaveBeenCalledTimes(1)
      expect(getGamification).toHaveBeenCalledTimes(1)
      expect(getWeeklyTrend).toHaveBeenCalledTimes(1)
    })

    // After data is loaded, no further API calls should fire
    expect(getProfile.mock.calls.length).toBe(1)
    expect(getTodayLog.mock.calls.length).toBe(1)
  })
})

// ── DASH-11 ───────────────────────────────────────────────────────────────────

describe('DASH-11: userId read from localStorage — never hardcoded', () => {
  it('uses zerofy_user_id from localStorage for getTodayLog', async () => {
    const customId = 'user-from-localstorage-abc123'
    localStorage.setItem('zerofy_user_id', customId)

    renderDashboard()

    await waitFor(() => {
      expect(getTodayLog).toHaveBeenCalledWith(customId)
    })
  })

  it('uses zerofy_user_id from localStorage for getGamification', async () => {
    const customId = 'another-localstorage-uid'
    localStorage.setItem('zerofy_user_id', customId)

    renderDashboard()

    await waitFor(() => {
      expect(getGamification).toHaveBeenCalledWith(customId)
    })
  })
})

// ── DASH-12 ───────────────────────────────────────────────────────────────────

describe('DASH-12: axe-core scan → 0 critical or serious accessibility violations', () => {
  it('has no critical or serious axe violations after data loads', async () => {
    const { container } = renderDashboard()

    await waitFor(() => {
      expect(screen.getByTestId('score-breakdown')).not.toBeNull()
    })

    const results = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false } },
    })

    const serious = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    )

    if (serious.length > 0) {
      const summary = serious.map((v) => `${v.id}: ${v.description}`).join('\n')
      throw new Error(`axe found ${serious.length} violation(s):\n${summary}`)
    }

    expect(serious).toHaveLength(0)
  })
})
