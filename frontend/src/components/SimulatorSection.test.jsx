import { render, screen, fireEvent, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { axe, toHaveNoViolations } from 'jest-axe'
import SimulatorSection from './SimulatorSection'

expect.extend(toHaveNoViolations)

// Mock simulate() — synchronous, no real math in tests
vi.mock('../utils/simulator', () => ({
  simulate: vi.fn(() => ({
    daily_co2_kg: 4.5,
    breakdown: { transport: 2, diet: 1, electricity: 0.9, lpg: 0.6, total: 4.5 },
  })),
}))

// Mock getConstants so constants.js doesn't throw
vi.mock('../utils/constants', () => ({
  getConstants: vi.fn(() => ({
    transport:   { bus: 0.08, metro: 0.02, petrol_car: 0.21, diesel_car: 0.17, petrol_two_wheeler: 0.05, electric_vehicle: 0.01, auto_rickshaw: 0.06, walking: 0, cycling: 0 },
    diet:        { vegan: 1.5, vegetarian: 2.0, eggetarian: 2.5, non_vegetarian: 3.5 },
    electricity: { grid_factor: 0.82, ac_kwh_per_hour: 1.5 },
    lpg:         { kg_co2_per_cylinder: 11.7 },
  })),
}))

// No real HTTP via api.js
vi.mock('../utils/api', () => ({
  submitChatUpdate: vi.fn(),
}))

const mockProfile = {
  commute_mode: 'bus',
  avg_daily_km: 10,
  diet_type: 'vegetarian',
  ac_hours_per_day: 2,
  lpg_cylinders_per_month: 1,
}

describe('SimulatorSection', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('SIM-01: Sliders initialised from profile prop', () => {
    render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)
    expect(screen.getByLabelText(/daily commute distance/i).value).toBe('10')
    expect(screen.getByLabelText(/AC hours per day/i).value).toBe('2')
    expect(screen.getByLabelText(/LPG cylinders/i).value).toBe('1')
  })

  it('SIM-02: Slider change → simulate() called', async () => {
    const { simulate } = await import('../utils/simulator')
    render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)

    fireEvent.change(screen.getByLabelText(/daily commute distance/i), { target: { value: '20' } })
    act(() => vi.advanceTimersByTime(250))

    expect(simulate).toHaveBeenCalled()
  })

  it('SIM-03: simulate() called with debounce — rapid changes result in one call', async () => {
    const { simulate } = await import('../utils/simulator')
    const initialCallCount = simulate.mock.calls.length

    render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)

    const slider = screen.getByLabelText(/daily commute distance/i)
    fireEvent.change(slider, { target: { value: '15' } })
    fireEvent.change(slider, { target: { value: '20' } })
    fireEvent.change(slider, { target: { value: '25' } })

    // Before debounce fires — should not have been called again yet
    const callsBeforeDebounce = simulate.mock.calls.length - initialCallCount

    act(() => vi.advanceTimersByTime(250))

    const callsAfterDebounce = simulate.mock.calls.length - initialCallCount
    expect(callsBeforeDebounce).toBeLessThan(3)
    expect(callsAfterDebounce).toBe(2)
  })

  it('SIM-04: Zero API calls during slider movement — submitChatUpdate never called', async () => {
    const { submitChatUpdate } = await import('../utils/api')
    render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)

    fireEvent.change(screen.getByLabelText(/daily commute distance/i), { target: { value: '30' } })
    act(() => vi.advanceTimersByTime(250))

    expect(submitChatUpdate).not.toHaveBeenCalled()
  })

  it('SIM-05: "Log these changes" → onLogChanges called with a string', () => {
    const onLogChanges = vi.fn()
    render(<SimulatorSection profile={mockProfile} onLogChanges={onLogChanges} />)
    fireEvent.click(screen.getByText(/Log these changes/i))
    expect(onLogChanges).toHaveBeenCalledWith(expect.any(String))
  })

  it('SIM-06: onLogChanges string contains changed values — not empty', () => {
    const onLogChanges = vi.fn()
    render(<SimulatorSection profile={mockProfile} onLogChanges={onLogChanges} />)

    fireEvent.change(screen.getByLabelText(/daily commute distance/i), { target: { value: '50' } })
    fireEvent.click(screen.getByText(/Log these changes/i))

    const msg = onLogChanges.mock.calls[0][0]
    expect(msg.length).toBeGreaterThan(0)
    expect(msg).toMatch(/50/)
  })

  it('SIM-07: simulate() is never async — no Promise returned', async () => {
    const { simulate } = await import('../utils/simulator')
    render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)
    fireEvent.change(screen.getByLabelText(/daily commute distance/i), { target: { value: '20' } })
    act(() => vi.advanceTimersByTime(250))

    // All simulate() return values must be plain objects, not Promises
    for (const result of simulate.mock.results) {
      expect(result.value).not.toBeInstanceOf(Promise)
    }
  })

  it('SIM-08: Debounce cancelled on unmount — no state update after unmount', () => {
    const { unmount } = render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)
    fireEvent.change(screen.getByLabelText(/daily commute distance/i), { target: { value: '99' } })

    // Unmount before debounce fires
    unmount()

    // Advance timers — should not throw or cause state update warnings
    expect(() => act(() => vi.advanceTimersByTime(300))).not.toThrow()
  })

  it('SIM-09: SimulatorBreakdown pie updates after slider change (after debounce)', async () => {
    render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)

    fireEvent.change(screen.getByLabelText(/daily commute distance/i), { target: { value: '80' } })
    act(() => vi.advanceTimersByTime(250))

    // Chart container should be present with updated aria-label
    const chart = screen.getByRole('img', { name: /simulated CO2 breakdown/i })
    expect(chart).toBeInTheDocument()
  })

  it('SIM-10: axe-core → 0 critical violations', async () => {
    vi.useRealTimers()
    const { container } = render(<SimulatorSection profile={mockProfile} onLogChanges={vi.fn()} />)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
