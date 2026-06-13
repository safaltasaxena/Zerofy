import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { axe, toHaveNoViolations } from 'jest-axe'
import QuickUpdateForm from './QuickUpdateForm'

expect.extend(toHaveNoViolations)

describe('QuickUpdateForm', () => {
  const prefills = {
    commute_mode: 'bus',
    avg_daily_km: 10,
    ac_hours_per_day: 2,
    diet_type: 'vegan'
  }

  it('QUICK-01: All 4 fields render pre-filled', () => {
    render(<QuickUpdateForm prefills={prefills} onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/Commute Mode/i).value).toBe('bus')
    expect(screen.getByLabelText(/Distance/i).value).toBe('10')
    expect(screen.getByLabelText(/AC Hours/i).value).toBe('2')
    expect(screen.getByLabelText(/Diet/i).value).toBe('vegan')
  })

  it('QUICK-02: onSubmit called with correct values', () => {
    const onSubmit = vi.fn()
    render(<QuickUpdateForm prefills={prefills} onSubmit={onSubmit} />)
    fireEvent.click(screen.getByText(/Update my habits/i))
    expect(onSubmit).toHaveBeenCalledWith({
      commute_mode: 'bus',
      avg_daily_km: '10',
      ac_hours_per_day: '2',
      diet_type: 'vegan'
    })
  })

  it('QUICK-03: Every input has associated label', () => {
    render(<QuickUpdateForm prefills={prefills} onSubmit={vi.fn()} />)
    expect(screen.getByLabelText(/Commute Mode/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Distance/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/AC Hours/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Diet/i)).toBeInTheDocument()
  })

  it('QUICK-04: aria-busy on button during loading', () => {
    render(<QuickUpdateForm prefills={prefills} onSubmit={vi.fn()} isLoading={true} />)
    expect(screen.getByText(/Updating.../i)).toHaveAttribute('aria-busy', 'true')
  })

  it('QUICK-05: avg_daily_km > 500 → exact error message', () => {
    render(<QuickUpdateForm prefills={{ ...prefills, avg_daily_km: 600 }} onSubmit={vi.fn()} />)
    fireEvent.click(screen.getByText(/Update my habits/i))
    expect(screen.getByText('Enter a distance between 0 and 500 km')).toBeInTheDocument()
  })

  it('QUICK-06: axe-core → 0 critical violations', async () => {
    const { container } = render(<QuickUpdateForm prefills={prefills} onSubmit={vi.fn()} />)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
