import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { axe, toHaveNoViolations } from 'jest-axe'
import ChatSection from './ChatSection'
import * as api from '../utils/api'

expect.extend(toHaveNoViolations)

vi.mock('../utils/api', () => ({
  submitChatUpdate: vi.fn()
}))

describe('ChatSection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
  })

  const mockProfile = { commute_mode: 'bus', avg_daily_km: 10, ac_hours_per_day: 2, diet_type: 'vegan' }

  it('CHAT-01: submitChatUpdate called with emoji-preprocessed text', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({ confidence: 'low' })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'I took the 🚇 today' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    await waitFor(() => {
      expect(api.submitChatUpdate).toHaveBeenCalledWith('I took the metro today')
    })
  })

  it('CHAT-02: 🚇 → "metro" before API call', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({ confidence: 'low' })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: '🚇' } })
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })
    await waitFor(() => expect(api.submitChatUpdate).toHaveBeenCalledWith('metro'))
  })

  it('CHAT-03: High confidence → ParsePreview shown', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({
      confidence: 'high',
      preview: { category: 'Transport', change: 'metro', quantity: 10, unit: 'km' }
    })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'metro 10km' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    await waitFor(() => {
      expect(screen.getByText('Transport → metro | 10 km')).toBeInTheDocument()
    })
  })

  it('CHAT-04: Low confidence turn 1 → follow-up shown', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({
      confidence: 'low',
      bot_reply: 'Could you clarify?'
    })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'stuff' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    await waitFor(() => {
      expect(screen.getByText('Could you clarify?')).toBeInTheDocument()
    })
    expect(screen.queryByLabelText(/Quick Update Form/i)).not.toBeInTheDocument()
  })

  it('CHAT-05: Low confidence turn 2 → QuickUpdateForm shown immediately', async () => {
    api.submitChatUpdate.mockResolvedValue({ confidence: 'low', bot_reply: 'Can you clarify?' })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)

    // Turn 1 — low confidence → follow-up shown, form NOT visible
    const input1 = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input1, { target: { value: 'turn one' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    await waitFor(() => expect(screen.getByText('Can you clarify?')).toBeInTheDocument())
    expect(screen.queryByLabelText(/Quick Update Form/i)).not.toBeInTheDocument()

    // Turn 2 — low confidence → QuickUpdateForm should appear
    const input2 = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input2, { target: { value: 'turn two' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    await waitFor(() => {
      expect(screen.getByLabelText(/Quick Update Form/i)).toBeInTheDocument()
    })
  })

  it('CHAT-06: Confirm ParsePreview → onUpdateConfirmed called', async () => {
    const onUpdateConfirmed = vi.fn()
    api.submitChatUpdate.mockResolvedValueOnce({
      confidence: 'high',
      preview: { category: 'Transport', change: 'metro', quantity: 10, unit: 'km' }
    })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={onUpdateConfirmed} />)
    
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'metro 10km' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Confirm ✅'))
    })
    
    expect(onUpdateConfirmed).toHaveBeenCalled()
  })

  it('CHAT-07: Input disabled during loading', async () => {
    api.submitChatUpdate.mockImplementationOnce(() => new Promise(() => {}))
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'hello' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    expect(input).toBeDisabled()
  })

  it('CHAT-08: Enter key submits', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({ confidence: 'low' })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'hello' } })
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })
    
    await waitFor(() => {
      expect(api.submitChatUpdate).toHaveBeenCalled()
    })
  })

  it('CHAT-09: Message over 500 chars → submit blocked', async () => {
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    const longText = 'a'.repeat(501)
    fireEvent.change(input, { target: { value: longText } })
    expect(input.value.length).toBeLessThanOrEqual(500)
  })

  it('CHAT-10: Negative delta → celebratory message', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({
      confidence: 'high',
      delta_kg: -5.5,
      preview: { category: 'Transport', change: 'metro', quantity: 10, unit: 'km' }
    })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'metro 10km' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    await waitFor(() => fireEvent.click(screen.getByText('Confirm ✅')))
    await waitFor(() => expect(screen.getByText(/You saved 5.50 kg today/i)).toBeInTheDocument())
  })

  it('CHAT-11: Positive delta → non-judgmental message', async () => {
    api.submitChatUpdate.mockResolvedValueOnce({
      confidence: 'high',
      delta_kg: 2.0,
      preview: { category: 'Transport', change: 'car', quantity: 10, unit: 'km' }
    })
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    
    const input = screen.getByPlaceholderText(/Tell me about your day/i)
    fireEvent.change(input, { target: { value: 'car 10km' } })
    fireEvent.click(screen.getByRole('button', { name: /Send/i }))
    
    await waitFor(() => fireEvent.click(screen.getByText('Confirm ✅')))
    await waitFor(() => expect(screen.getByText(/A bit higher today — that's okay/i)).toBeInTheDocument())
  })

  it('CHAT-12: Bot replies in aria-live="polite" region', () => {
    render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const region = screen.getByRole('log')
    expect(region).toHaveAttribute('aria-live', 'polite')
  })

  it('CHAT-13: axe-core → 0 critical violations', async () => {
    const { container } = render(<ChatSection profile={mockProfile} onUpdateConfirmed={vi.fn()} />)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
