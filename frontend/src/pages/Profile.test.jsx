import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axe from 'axe-core'
import Profile from './Profile'
import { getProfile, getGamification } from '../utils/api'

// Mock navigate hook
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock the API calls
vi.mock('../utils/api', () => ({
  getProfile: vi.fn(),
  getGamification: vi.fn(),
}))

const mockProfileData = {
  name: 'Aryan Verma',
  state: 'Delhi',
  city: 'New Delhi',
  commute_mode: 'metro',
  avg_daily_km: 15,
  diet_type: 'vegan',
  ac_hours_per_day: 4,
  lpg_cylinders_per_month: 1,
}

const mockGamificationData = {
  log_streak: 5,
  awareness_score: 150,
  badges: ['First Step', 'Quiz Master'],
}

function renderProfile() {
  return render(
    <MemoryRouter>
      <Profile />
    </MemoryRouter>
  )
}

describe('Profile Page Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    localStorage.setItem('zerofy_user_id', 'test-user-999')
  })

  // ── PROF-01 ──────────────────────────────────────────────────────────────────
  describe('PROF-01: Name, state, city rendered', () => {
    it('displays the user name and correct location text', async () => {
      getProfile.mockResolvedValueOnce(mockProfileData)
      getGamification.mockResolvedValueOnce(mockGamificationData)

      renderProfile()

      expect(await screen.findByText('Aryan Verma')).toBeTruthy()
      expect(screen.getByText('New Delhi, Delhi')).toBeTruthy()
    })
  })

  // ── PROF-02 ──────────────────────────────────────────────────────────────────
  describe('PROF-02: Streak and points rendered', () => {
    it('displays the gamified streak days and points earned', async () => {
      getProfile.mockResolvedValueOnce(mockProfileData)
      getGamification.mockResolvedValueOnce(mockGamificationData)

      renderProfile()

      expect(await screen.findByText(/5 days/i)).toBeTruthy()
      expect(screen.getByText(/150 pts/i)).toBeTruthy()
    })
  })

  // ── PROF-03 ──────────────────────────────────────────────────────────────────
  describe('PROF-03: BadgeShelf rendered with badges', () => {
    it('renders the badge list elements via BadgeShelf', async () => {
      getProfile.mockResolvedValueOnce(mockProfileData)
      getGamification.mockResolvedValueOnce(mockGamificationData)

      renderProfile()

      // The badges inside gamification are 'First Step' and 'Quiz Master'
      expect(await screen.findByText('First Step')).toBeTruthy()
      expect(screen.getByText('Quiz Master')).toBeTruthy()
    })
  })

  // ── PROF-04 ──────────────────────────────────────────────────────────────────
  describe('PROF-04: Both API calls made in parallel — Promise.all verified', () => {
    it('calls Promise.all to fetch profile and gamification parallelly', async () => {
      getProfile.mockResolvedValueOnce(mockProfileData)
      getGamification.mockResolvedValueOnce(mockGamificationData)
      const promiseAllSpy = vi.spyOn(Promise, 'all')

      renderProfile()

      await screen.findByText('Aryan Verma')
      expect(promiseAllSpy).toHaveBeenCalled()
      expect(getProfile).toHaveBeenCalledTimes(1)
      expect(getGamification).toHaveBeenCalledTimes(1)
      
      promiseAllSpy.mockRestore()
    })
  })

  // ── PROF-05 ──────────────────────────────────────────────────────────────────
  describe('PROF-05: "Update my habits" navigates to /onboarding', () => {
    it('routes to onboarding when update button is clicked', async () => {
      getProfile.mockResolvedValueOnce(mockProfileData)
      getGamification.mockResolvedValueOnce(mockGamificationData)

      renderProfile()

      const updateBtn = await screen.findByRole('button', { name: /Update my habits/i })
      await fireEvent.click(updateBtn)

      expect(mockNavigate).toHaveBeenCalledWith('/onboarding')
    })
  })

  // ── PROF-06 ──────────────────────────────────────────────────────────────────
  describe('PROF-06: axe-core → 0 critical violations', () => {
    it('has no critical or serious accessibility violations', async () => {
      getProfile.mockResolvedValueOnce(mockProfileData)
      getGamification.mockResolvedValueOnce(mockGamificationData)

      const { container } = renderProfile()
      await screen.findByText('Aryan Verma')

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
