import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axe from 'axe-core'

import LandingPage from '../pages/LandingPage'
import OnboardingForm from '../pages/OnboardingForm'
import Dashboard from '../pages/Dashboard'
import DailyQuiz from '../pages/DailyQuiz'
import Leaderboard from '../pages/Leaderboard'
import Profile from '../pages/Profile'

// Mock all API calls completely (no real HTTP)
vi.mock('../utils/api', () => ({
  getProfile: vi.fn(() => Promise.resolve({
    name: 'Test User',
    state: 'Maharashtra',
    city: 'Mumbai',
    commute_mode: 'metro',
    avg_daily_km: 10,
    diet_type: 'vegan',
    ac_hours_per_day: 2,
    lpg_cylinders_per_month: 0.5,
  })),
  getTodayLog: vi.fn(() => Promise.resolve({
    daily_co2_kg: 3.5,
    breakdown: { transport: 1.0, diet: 1.5, electricity: 1.0, lpg: 0.0, total: 3.5 },
    analogy: 'Like charging 400 phones 🔋',
    suggestions: ['Switch to LED', 'Carpool'],
  })),
  getGamification: vi.fn(() => Promise.resolve({
    log_streak: 5,
    awareness_score: 150,
    badges: ['First Step'],
  })),
  getWeeklyTrend: vi.fn(() => Promise.resolve([
    { date: '2026-06-10', daily_co2_kg: 3.5 },
  ])),
  getTodayQuiz: vi.fn(() => Promise.resolve({
    questions: [
      { question: 'Q1', options: ['A', 'B', 'C', 'D'], correct_index: 0, explanation: 'E1' },
      { question: 'Q2', options: ['E', 'F', 'G', 'H'], correct_index: 1, explanation: 'E2' },
      { question: 'Q3', options: ['I', 'J', 'K', 'L'], correct_index: 2, explanation: 'E3' },
    ],
    submitted: false,
  })),
  submitQuizAnswers: vi.fn(() => Promise.resolve({
    score: 3,
    points_earned: 15,
  })),
  getLeaderboard: vi.fn(() => Promise.resolve({
    leaderboard: [
      { user_id: 'test-user', name: 'Test User', awareness_score: 150, top_badge: 'First Step' },
      { user_id: 'user-2', name: 'Other User', awareness_score: 120, top_badge: 'Quiz Master' },
    ],
  })),
  fetchConstants: vi.fn(() => Promise.resolve({
    transport: { metro: 0.01 },
    diet: { vegan: 1.5 },
    electricity: { ac_kwh_per_hour: 1.5 },
    lpg: { kg_co2_per_cylinder: 12.0 },
  })),
}))

// Mock Firebase auth completely by setting up localStorage before each test
beforeEach(() => {
  localStorage.setItem('zerofy_token', 'mock-firebase-token')
  localStorage.setItem('zerofy_user_id', 'test-user')
  localStorage.setItem('zerofy_state', 'Maharashtra')
})

async function checkAccessibility(container) {
  const results = await axe.run(container, {
    rules: {
      'color-contrast': { enabled: false }, // jsdom does not support style calculation
    },
  })
  return results.violations
}

describe('Final Accessibility Audits', () => {
  // ── LandingPage ──
  describe('LandingPage A11y', () => {
    it('A11Y-FINAL-01: 0 critical axe violations on LandingPage', async () => {
      const { container } = render(
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      )
      const violations = await checkAccessibility(container)
      const critical = violations.filter(v => v.impact === 'critical')
      expect(critical).toHaveLength(0)
    })

    it('A11Y-FINAL-02: 0 serious axe violations on LandingPage', async () => {
      const { container } = render(
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      )
      const violations = await checkAccessibility(container)
      const serious = violations.filter(v => v.impact === 'serious')
      expect(serious).toHaveLength(0)
    })
  })

  // ── OnboardingForm ──
  describe('OnboardingForm A11y', () => {
    it('A11Y-FINAL-01: 0 critical axe violations on OnboardingForm', async () => {
      const { container } = render(
        <MemoryRouter>
          <OnboardingForm />
        </MemoryRouter>
      )
      const violations = await checkAccessibility(container)
      const critical = violations.filter(v => v.impact === 'critical')
      expect(critical).toHaveLength(0)
    })

    it('A11Y-FINAL-02: 0 serious axe violations on OnboardingForm', async () => {
      const { container } = render(
        <MemoryRouter>
          <OnboardingForm />
        </MemoryRouter>
      )
      const violations = await checkAccessibility(container)
      const serious = violations.filter(v => v.impact === 'serious')
      expect(serious).toHaveLength(0)
    })
  })

  // ── Dashboard ──
  describe('Dashboard A11y', () => {
    it('A11Y-FINAL-01: 0 critical axe violations on Dashboard', async () => {
      const { container } = render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      )
      // wait for content to load
      await screen.findByText(/Today/i)
      const violations = await checkAccessibility(container)
      const critical = violations.filter(v => v.impact === 'critical')
      expect(critical).toHaveLength(0)
    })

    it('A11Y-FINAL-02: 0 serious axe violations on Dashboard', async () => {
      const { container } = render(
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      )
      await screen.findByText(/Today/i)
      const violations = await checkAccessibility(container)
      const serious = violations.filter(v => v.impact === 'serious')
      expect(serious).toHaveLength(0)
    })
  })

  // ── DailyQuiz ──
  describe('DailyQuiz A11y', () => {
    it('A11Y-FINAL-01: 0 critical axe violations on DailyQuiz', async () => {
      const { container } = render(
        <MemoryRouter>
          <DailyQuiz />
        </MemoryRouter>
      )
      await screen.findByText(/Question 1 of 3/i)
      const violations = await checkAccessibility(container)
      const critical = violations.filter(v => v.impact === 'critical')
      expect(critical).toHaveLength(0)
    })

    it('A11Y-FINAL-02: 0 serious axe violations on DailyQuiz', async () => {
      const { container } = render(
        <MemoryRouter>
          <DailyQuiz />
        </MemoryRouter>
      )
      await screen.findByText(/Question 1 of 3/i)
      const violations = await checkAccessibility(container)
      const serious = violations.filter(v => v.impact === 'serious')
      expect(serious).toHaveLength(0)
    })
  })

  // ── Leaderboard ──
  describe('Leaderboard A11y', () => {
    it('A11Y-FINAL-01: 0 critical axe violations on Leaderboard', async () => {
      const { container } = render(
        <MemoryRouter>
          <Leaderboard />
        </MemoryRouter>
      )
      await screen.findByText(/Other/i)
      const violations = await checkAccessibility(container)
      const critical = violations.filter(v => v.impact === 'critical')
      expect(critical).toHaveLength(0)
    })

    it('A11Y-FINAL-02: 0 serious axe violations on Leaderboard', async () => {
      const { container } = render(
        <MemoryRouter>
          <Leaderboard />
        </MemoryRouter>
      )
      await screen.findByText(/Other/i)
      const violations = await checkAccessibility(container)
      const serious = violations.filter(v => v.impact === 'serious')
      expect(serious).toHaveLength(0)
    })
  })

  // ── Profile ──
  describe('Profile A11y', () => {
    it('A11Y-FINAL-01: 0 critical axe violations on Profile', async () => {
      const { container } = render(
        <MemoryRouter>
          <Profile />
        </MemoryRouter>
      )
      await screen.findByText(/My Profile/i)
      const violations = await checkAccessibility(container)
      const critical = violations.filter(v => v.impact === 'critical')
      expect(critical).toHaveLength(0)
    })

    it('A11Y-FINAL-02: 0 serious axe violations on Profile', async () => {
      const { container } = render(
        <MemoryRouter>
          <Profile />
        </MemoryRouter>
      )
      await screen.findByText(/My Profile/i)
      const violations = await checkAccessibility(container)
      const serious = violations.filter(v => v.impact === 'serious')
      expect(serious).toHaveLength(0)
    })
  })
})
