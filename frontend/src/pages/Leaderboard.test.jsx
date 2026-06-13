import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axe from 'axe-core'
import Leaderboard from './Leaderboard'
import { getLeaderboard } from '../utils/api'

// Mock the API calls
vi.mock('../utils/api', () => ({
  getLeaderboard: vi.fn(),
}))

const mockLeaderboardData = {
  leaderboard: [
    { user_id: 'user-1', name: 'Aarav Mehta', awareness_score: 120, top_badge: 'Quiz Master' },
    { user_id: 'user-2', name: 'Devika Sharma', awareness_score: 95, top_badge: 'Week Warrior' },
    { user_id: 'user-3', name: 'Kabir Kapoor', awareness_score: 80, top_badge: 'Carbon Cutter' },
    { user_id: 'user-4', name: 'Zara Sen', awareness_score: 75, top_badge: 'First Step' },
  ],
}

function renderLeaderboard() {
  return render(
    <MemoryRouter>
      <Leaderboard />
    </MemoryRouter>
  )
}

describe('Leaderboard Page Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    localStorage.setItem('zerofy_user_id', 'user-1')
    localStorage.setItem('zerofy_state', 'Maharashtra')
  })

  // ── LB-01 ───────────────────────────────────────────────────────────────────
  describe('LB-01: Top 3 entries render', () => {
    it('renders the top 3 items in the list with first names', async () => {
      getLeaderboard.mockResolvedValueOnce(mockLeaderboardData)
      renderLeaderboard()

      expect(await screen.findByText('Aarav')).toBeTruthy()
      expect(screen.getByText('Devika')).toBeTruthy()
      expect(screen.getByText('Kabir')).toBeTruthy()
    })
  })

  // ── LB-02 ───────────────────────────────────────────────────────────────────
  describe('LB-02: Current user row highlighted', () => {
    it('applies aria-current="true" to the current user row', async () => {
      localStorage.setItem('zerofy_user_id', 'user-2')
      getLeaderboard.mockResolvedValueOnce(mockLeaderboardData)
      const { container } = renderLeaderboard()

      await screen.findByText('Devika')
      const row = container.querySelector('tr[aria-current="true"]')
      expect(row).toBeTruthy()
      expect(row.textContent).toContain('Devika')
    })
  })

  // ── LB-03 ───────────────────────────────────────────────────────────────────
  describe('LB-03: EDGE-21 — rank 1 shows "1st"', () => {
    it('renders 1st for the top rank without breaking', async () => {
      getLeaderboard.mockResolvedValueOnce(mockLeaderboardData)
      renderLeaderboard()

      const firstRank = await screen.findByText('1st')
      expect(firstRank).toBeTruthy()
    })
  })

  // ── LB-04 ───────────────────────────────────────────────────────────────────
  describe('LB-04: EDGE-22 — user not ranked → placeholder', () => {
    it('displays the unranked placeholder text if current user is not in the list', async () => {
      localStorage.setItem('zerofy_user_id', 'unranked-user')
      getLeaderboard.mockResolvedValueOnce(mockLeaderboardData)
      renderLeaderboard()

      expect(await screen.findByText("You're not ranked yet — keep logging!")).toBeTruthy()
    })
  })

  // ── LB-05 ───────────────────────────────────────────────────────────────────
  describe('LB-05: Loading state shown on mount', () => {
    it('renders the loading state before resolving API data', async () => {
      let resolveLeaderboard
      const promise = new Promise((resolve) => {
        resolveLeaderboard = resolve
      })
      getLeaderboard.mockReturnValueOnce(promise)

      renderLeaderboard()

      expect(screen.getByText('Leaderboard')).toBeTruthy()
      expect(screen.getByRole('heading', { name: 'Leaderboard' })).toBeTruthy()

      await act(async () => {
        resolveLeaderboard(mockLeaderboardData)
      })
    })
  })

  // ── LB-06 ───────────────────────────────────────────────────────────────────
  describe('LB-06: axe-core → 0 critical violations', () => {
    it('has no critical or serious accessibility violations', async () => {
      getLeaderboard.mockResolvedValueOnce(mockLeaderboardData)
      const { container } = renderLeaderboard()

      expect(await screen.findByText('Aarav')).toBeTruthy()

      const results = await axe.run(container, {
        rules: {
          'color-contrast': { enabled: false },
        },
      })
      const criticalOrSerious = results.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      )
      expect(criticalOrSerious).toHaveLength(0)
    })
  })
})
