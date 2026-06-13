import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axe from 'axe-core'
import DailyQuiz from './DailyQuiz'
import { getTodayQuiz, submitQuizAnswers } from '../utils/api'

// Mock the API calls
vi.mock('../utils/api', () => ({
  getTodayQuiz: vi.fn(),
  submitQuizAnswers: vi.fn(),
}))

const mockQuestions = [
  { question: 'Question 1', options: ['A', 'B', 'C', 'D'], correct_index: 0, explanation: 'Exp 1' },
  { question: 'Question 2', options: ['E', 'F', 'G', 'H'], correct_index: 1, explanation: 'Exp 2' },
  { question: 'Question 3', options: ['I', 'J', 'K', 'L'], correct_index: 2, explanation: 'Exp 3' },
]

function renderQuiz() {
  return render(
    <MemoryRouter>
      <DailyQuiz />
    </MemoryRouter>
  )
}

describe('DailyQuiz Page Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    localStorage.setItem('zerofy_user_id', 'test-user-123')
  })

  // ── QUIZ-01 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-01: Questions render on load', () => {
    it('loads and displays the first question', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      renderQuiz()

      expect(await screen.findByText('Question 1 of 3')).toBeTruthy()
      expect(screen.getByText('Question 1')).toBeTruthy()
      expect(screen.getByRole('button', { name: 'A' })).toBeTruthy()
    })
  })

  // ── QUIZ-02 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-02: Already completed → locked message shown', () => {
    it('shows the locked message if the quiz has already been submitted today', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: [], submitted: true })
      renderQuiz()

      expect(await screen.findByText(/You've already completed today's quiz/i)).toBeTruthy()
      expect(screen.queryByText('Question 1 of 3')).toBeNull()
    })
  })

  // ── QUIZ-03 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-03: Selecting answer highlights it', () => {
    it('changes the aria-pressed state on selection', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      renderQuiz()

      const optionA = await screen.findByRole('button', { name: 'A' })
      expect(optionA.getAttribute('aria-pressed')).toBe('false')

      await fireEvent.click(optionA)
      expect(optionA.getAttribute('aria-pressed')).toBe('true')
    })
  })

  // ── QUIZ-04 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-04: After question 3 → submitQuizAnswers called', () => {
    it('sends the selected answer indices to the API', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      submitQuizAnswers.mockResolvedValueOnce({ success: true, data: { score: 3, points_earned: 15 } })
      renderQuiz()

      // Q1
      const optA = await screen.findByRole('button', { name: 'A' })
      await fireEvent.click(optA)
      const nextBtn1 = screen.getByRole('button', { name: 'Next' })
      await fireEvent.click(nextBtn1)

      // Q2
      const optF = await screen.findByRole('button', { name: 'F' })
      await fireEvent.click(optF)
      const nextBtn2 = screen.getByRole('button', { name: 'Next' })
      await fireEvent.click(nextBtn2)

      // Q3
      const optK = await screen.findByRole('button', { name: 'K' })
      await fireEvent.click(optK)
      const submitBtn = screen.getByRole('button', { name: 'Submit' })
      await fireEvent.click(submitBtn)

      expect(submitQuizAnswers).toHaveBeenCalledWith([0, 1, 2])
    })
  })

  // ── QUIZ-05 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-05: ResultCard shown after submit', () => {
    it('renders the result card upon successful submission', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      submitQuizAnswers.mockResolvedValueOnce({ success: true, data: { score: 3, points_earned: 15 } })
      renderQuiz()

      await fireEvent.click(await screen.findByRole('button', { name: 'A' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Next' }))
      await fireEvent.click(await screen.findByRole('button', { name: 'F' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Next' }))
      await fireEvent.click(await screen.findByRole('button', { name: 'K' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

      expect(await screen.findByText('You got 3 out of 3')).toBeTruthy()
      expect(screen.getByText('+15 Points')).toBeTruthy()
    })
  })

  // ── QUIZ-06 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-06: Score displayed correctly', () => {
    it('calculates and shows correct and points count for partial answers', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      submitQuizAnswers.mockResolvedValueOnce({ success: true, data: { score: 2, points_earned: 10 } })
      renderQuiz()

      // Q1: correct (A -> index 0 matches 0)
      await fireEvent.click(await screen.findByRole('button', { name: 'A' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Next' }))

      // Q2: correct (F -> index 1 matches 1)
      await fireEvent.click(await screen.findByRole('button', { name: 'F' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Next' }))

      // Q3: wrong (I -> index 0 matches 2 is false)
      await fireEvent.click(await screen.findByRole('button', { name: 'I' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

      expect(await screen.findByText('You got 2 out of 3')).toBeTruthy()
      expect(screen.getByText('+10 Points')).toBeTruthy()
    })
  })

  // ── QUIZ-07 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-07: Double submit blocked by isLoading', () => {
    it('blocks double submits while submission is active', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      let resolveSubmit
      const promise = new Promise((resolve) => {
        resolveSubmit = resolve
      })
      submitQuizAnswers.mockReturnValueOnce(promise)

      renderQuiz()

      await fireEvent.click(await screen.findByRole('button', { name: 'A' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Next' }))
      await fireEvent.click(await screen.findByRole('button', { name: 'F' }))
      await fireEvent.click(screen.getByRole('button', { name: 'Next' }))
      await fireEvent.click(await screen.findByRole('button', { name: 'K' }))

      const submitBtn = screen.getByRole('button', { name: 'Submit' })
      await fireEvent.click(submitBtn)
      await fireEvent.click(submitBtn) // Double click

      expect(submitQuizAnswers).toHaveBeenCalledTimes(1)

      await act(async () => {
        resolveSubmit({ success: true, data: { score: 3, points_earned: 15 } })
      })
    })
  })

  // ── QUIZ-08 ───────────────────────────────────────────────────────────────────
  describe('QUIZ-08: axe-core → 0 critical violations', () => {
    it('has no critical or serious accessibility violations', async () => {
      getTodayQuiz.mockResolvedValueOnce({ questions: mockQuestions, submitted: false })
      const { container } = renderQuiz()

      expect(await screen.findByText('Question 1 of 3')).toBeTruthy()

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
