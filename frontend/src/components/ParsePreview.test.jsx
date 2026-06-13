import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ParsePreview from './ParsePreview'

describe('ParsePreview', () => {
  const mockPreview = {
    category: 'Commute',
    change: 'metro',
    quantity: 15,
    unit: 'km'
  }

  it('PREV-01: Renders category, change, quantity, unit', () => {
    render(<ParsePreview preview={mockPreview} onConfirm={vi.fn()} onEdit={vi.fn()} />)
    expect(screen.getByText('Commute → metro | 15 km')).toBeInTheDocument()
  })

  it('PREV-02: Confirm aria-label correct', () => {
    render(<ParsePreview preview={mockPreview} onConfirm={vi.fn()} onEdit={vi.fn()} />)
    expect(screen.getByLabelText('Confirm: metro 15 km')).toBeInTheDocument()
  })

  it('PREV-03: Edit aria-label="Edit this update"', () => {
    render(<ParsePreview preview={mockPreview} onConfirm={vi.fn()} onEdit={vi.fn()} />)
    expect(screen.getByLabelText('Edit this update')).toBeInTheDocument()
  })

  it('PREV-04: onConfirm called on Confirm click', () => {
    const onConfirm = vi.fn()
    render(<ParsePreview preview={mockPreview} onConfirm={onConfirm} onEdit={vi.fn()} />)
    fireEvent.click(screen.getByText('Confirm ✅'))
    expect(onConfirm).toHaveBeenCalled()
  })

  it('PREV-05: onEdit called on Edit click', () => {
    const onEdit = vi.fn()
    render(<ParsePreview preview={mockPreview} onConfirm={vi.fn()} onEdit={onEdit} />)
    fireEvent.click(screen.getByText('Edit ✏️'))
    expect(onEdit).toHaveBeenCalled()
  })

  it('PREV-06: Enter triggers onConfirm', () => {
    const onConfirm = vi.fn()
    render(<ParsePreview preview={mockPreview} onConfirm={onConfirm} onEdit={vi.fn()} />)
    fireEvent.keyDown(screen.getByText('Confirm ✅'), { key: 'Enter', code: 'Enter' })
    expect(onConfirm).toHaveBeenCalled()
  })
})
