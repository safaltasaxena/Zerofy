/**
 * OnboardingForm.test.jsx — Tests for OnboardingForm.jsx
 *
 * ONB-01: all 10 fields render
 * ONB-02: valid submit → calls submitOnboarding with correct shape
 * ONB-03: success → navigates to /dashboard
 * ONB-04: API error → shows error message
 * ONB-05: loading state — button shows "Saving..." + aria-busy="true"
 * ONB-06: honeypot filled → submitOnboarding NOT called
 * ONB-07: double submit blocked during loading
 * ONB-08: avg_daily_km > 500 → exact error message shown inline
 * ONB-09: commute_mode not selected → exact error message shown
 * ONB-10: every input has associated <label>
 * ONB-11: axe-core scan → 0 critical or serious violations
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axe from 'axe-core'

// ── Mock react-router-dom navigate ────────────────────────────────────────────

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// ── Mock api.js ───────────────────────────────────────────────────────────────

vi.mock('../utils/api', () => ({
  submitOnboarding: vi.fn(),
}))

import { submitOnboarding } from '../utils/api'
import OnboardingForm from './OnboardingForm'

// ── Render helper ─────────────────────────────────────────────────────────────

function renderForm() {
  return render(
    <MemoryRouter>
      <OnboardingForm />
    </MemoryRouter>
  )
}

// ── Valid form data ───────────────────────────────────────────────────────────

const VALID = {
  name: 'Priya Sharma',
  state: 'Maharashtra',
  city: 'Mumbai',
  commute_mode: 'metro',
  avg_daily_km: '12',
  diet_type: 'vegetarian',
  ac_hours_per_day: '2',
  monthly_electricity_units: '150',
  lpg_cylinders_per_month: '1',
  persona: 'professional',
}

/**
 * Fill all form fields with the given values object.
 * Skips honeypot field — that is filled separately in ONB-06.
 */
function fillForm(container, values = VALID) {
  const setField = (id, value) => {
    const el = container.querySelector(`#${id}`)
    if (!el) return
    fireEvent.change(el, { target: { value } })
  }

  setField('name', values.name)
  setField('state', values.state)
  setField('city', values.city)
  setField('commute_mode', values.commute_mode)
  setField('avg_daily_km', values.avg_daily_km)
  setField('diet_type', values.diet_type)
  setField('ac_hours_per_day', values.ac_hours_per_day)
  setField('monthly_electricity_units', values.monthly_electricity_units)
  setField('lpg_cylinders_per_month', values.lpg_cylinders_per_month)
  setField('persona', values.persona)
}

function submitForm(container) {
  fireEvent.submit(container.querySelector('form'))
}

// ── beforeEach ────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  submitOnboarding.mockResolvedValue({ profile: {} })
})

// ── ONB-01 ────────────────────────────────────────────────────────────────────

describe('ONB-01: all 10 fields render', () => {
  it('renders all required field inputs', () => {
    const { container } = renderForm()
    const fieldIds = [
      'name', 'state', 'city', 'commute_mode',
      'avg_daily_km', 'diet_type', 'ac_hours_per_day',
      'monthly_electricity_units', 'lpg_cylinders_per_month', 'persona',
    ]
    fieldIds.forEach((id) => {
      const el = container.querySelector(`#${id}`)
      expect(el, `Missing field: #${id}`).not.toBeNull()
    })
  })
})

// ── ONB-02 ────────────────────────────────────────────────────────────────────

describe('ONB-02: valid submit calls submitOnboarding with correct shape', () => {
  it('calls submitOnboarding including monthly_electricity_units', async () => {
    const { container } = renderForm()
    fillForm(container)
    await act(async () => { submitForm(container) })

    await waitFor(() => {
      expect(submitOnboarding).toHaveBeenCalledTimes(1)
    })

    const payload = submitOnboarding.mock.calls[0][0]
    expect(payload).toMatchObject({
      name: 'Priya Sharma',
      state: 'Maharashtra',
      city: 'Mumbai',
      commute_mode: 'metro',
      avg_daily_km: 12,
      diet_type: 'vegetarian',
      ac_hours_per_day: 2,
      monthly_electricity_units: 150,
      lpg_cylinders_per_month: 1,
      persona: 'professional',
    })
  })
})

// ── ONB-03 ────────────────────────────────────────────────────────────────────

describe('ONB-03: success → navigates to /dashboard', () => {
  it('calls navigate("/dashboard") after successful submit', async () => {
    const { container } = renderForm()
    fillForm(container)
    await act(async () => { submitForm(container) })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })
})

// ── ONB-04 ────────────────────────────────────────────────────────────────────

describe('ONB-04: API error → shows error message', () => {
  it('shows network error message on API failure', async () => {
    submitOnboarding.mockRejectedValue(new Error('Network failed'))
    const { container } = renderForm()
    fillForm(container)
    await act(async () => { submitForm(container) })

    await waitFor(() => {
      const error = container.querySelector('[role="alert"]')
      expect(error).not.toBeNull()
      expect(error.textContent).toContain("Couldn't save right now")
    })
  })

  it('does not navigate on error', async () => {
    submitOnboarding.mockRejectedValue(new Error('Network failed'))
    const { container } = renderForm()
    fillForm(container)
    await act(async () => { submitForm(container) })

    await waitFor(() => {
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })
})

// ── ONB-05 ────────────────────────────────────────────────────────────────────

describe('ONB-05: loading state — button text and aria-busy', () => {
  it('shows "Saving..." during loading and aria-busy="true"', async () => {
    // Make the API call hang so we can catch the loading state
    let resolveOnboarding
    submitOnboarding.mockImplementation(
      () => new Promise((resolve) => { resolveOnboarding = resolve })
    )

    const { container } = renderForm()
    fillForm(container)

    act(() => { submitForm(container) })

    await waitFor(() => {
      const btn = container.querySelector('button[type="submit"]')
      expect(btn.textContent).toBe('Saving...')
      expect(btn.getAttribute('aria-busy')).toBe('true')
    })

    // Clean up — resolve the hanging promise
    await act(async () => { resolveOnboarding({ profile: {} }) })
  })
})

// ── ONB-06 ────────────────────────────────────────────────────────────────────

describe('ONB-06: honeypot filled → submitOnboarding NOT called', () => {
  it('silently drops submission when honeypot is filled', async () => {
    const { container } = renderForm()
    fillForm(container)

    // Fill the honeypot field (hidden from real users)
    const honeypot = container.querySelector('input[name="website"]')
    expect(honeypot).not.toBeNull()
    fireEvent.change(honeypot, { target: { value: 'http://spam.com' } })

    await act(async () => { submitForm(container) })

    // Must not call the API
    expect(submitOnboarding).not.toHaveBeenCalled()
    // Must not show any error to the user
    const alerts = container.querySelectorAll('[role="alert"]')
    expect(alerts.length).toBe(0)
  })
})

// ── ONB-07 ────────────────────────────────────────────────────────────────────

describe('ONB-07: double submit blocked during loading', () => {
  it('calls submitOnboarding only once even when form submitted twice', async () => {
    let resolveOnboarding
    submitOnboarding.mockImplementation(
      () => new Promise((resolve) => { resolveOnboarding = resolve })
    )

    const { container } = renderForm()
    fillForm(container)

    act(() => { submitForm(container) })

    await waitFor(() => {
      const btn = container.querySelector('button[type="submit"]')
      expect(btn.getAttribute('aria-busy')).toBe('true')
    })

    // Second submit while loading
    act(() => { submitForm(container) })

    await act(async () => { resolveOnboarding({ profile: {} }) })

    expect(submitOnboarding).toHaveBeenCalledTimes(1)
  })
})

// ── ONB-08 ────────────────────────────────────────────────────────────────────

describe('ONB-08: avg_daily_km > 500 → exact ACCESSIBILITY.md error message', () => {
  it('shows inline error with exact spec message', async () => {
    const { container } = renderForm()
    fillForm(container, { ...VALID, avg_daily_km: '501' })
    await act(async () => { submitForm(container) })

    await waitFor(() => {
      const err = container.querySelector('#avg_daily_km-error')
      expect(err).not.toBeNull()
      expect(err.textContent).toBe('Enter a distance between 0 and 500 km')
    })
  })

  it('does not call API when validation fails', async () => {
    const { container } = renderForm()
    fillForm(container, { ...VALID, avg_daily_km: '501' })
    await act(async () => { submitForm(container) })
    expect(submitOnboarding).not.toHaveBeenCalled()
  })
})

// ── ONB-09 ────────────────────────────────────────────────────────────────────

describe('ONB-09: commute_mode not selected → exact ACCESSIBILITY.md error message', () => {
  it('shows inline error with exact spec message', async () => {
    const { container } = renderForm()
    fillForm(container, { ...VALID, commute_mode: '' })
    await act(async () => { submitForm(container) })

    await waitFor(() => {
      const err = container.querySelector('#commute_mode-error')
      expect(err).not.toBeNull()
      expect(err.textContent).toBe('Please select your main way of getting around')
    })
  })
})

// ── ONB-10 ────────────────────────────────────────────────────────────────────

describe('ONB-10: every input has associated <label>', () => {
  it('every input, select, and textarea has a corresponding label', () => {
    const { container } = renderForm()
    const inputs = container.querySelectorAll('input:not([aria-hidden="true"]), select, textarea')

    inputs.forEach((input) => {
      const id = input.getAttribute('id')
      if (!id) return  // honeypot has no id

      const label = container.querySelector(`label[for="${id}"]`)
      const ariaLabel = input.getAttribute('aria-label')
      const ariaLabelledBy = input.getAttribute('aria-labelledby')

      const isLabelled = label !== null || Boolean(ariaLabel) || Boolean(ariaLabelledBy)
      expect(isLabelled, `Input #${id} has no accessible label`).toBe(true)
    })
  })
})

// ── ONB-11 ────────────────────────────────────────────────────────────────────

describe('ONB-11: axe-core scan — 0 critical or serious violations', () => {
  it('has no critical or serious axe violations', async () => {
    const { container } = renderForm()

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious'
    )

    if (criticalOrSerious.length > 0) {
      const summary = criticalOrSerious.map((v) => `${v.id}: ${v.description}`).join('\n')
      throw new Error(`axe found ${criticalOrSerious.length} violation(s):\n${summary}`)
    }

    expect(criticalOrSerious).toHaveLength(0)
  })
})
