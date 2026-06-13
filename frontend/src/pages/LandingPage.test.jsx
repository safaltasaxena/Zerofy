/**
 * LandingPage.test.jsx — Tests for LandingPage.jsx
 *
 * LAND-01: renders <h1> headline text
 * LAND-02: "Get Started" navigates to /onboarding
 * LAND-03: "Sign In" navigates to /login
 * LAND-04: skip link is first focusable element
 * LAND-05: axe-core scan → 0 critical or serious accessibility violations
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import axe from 'axe-core'
import LandingPage from './LandingPage'

// ── Test helper — render with router context ──────────────────────────────────

function renderPage(initialEntry = '/') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <LandingPage />
    </MemoryRouter>
  )
}

// ── LAND-01 ───────────────────────────────────────────────────────────────────

describe('LAND-01: renders <h1> headline text', () => {
  it('contains the expected h1 text', () => {
    renderPage()
    const h1 = screen.getByRole('heading', { level: 1 })
    expect(h1).toBeTruthy()
    expect(h1.textContent).toContain('Track your carbon footprint')
    expect(h1.textContent).toContain('Indian style')
  })

  it('has exactly one h1 on the page', () => {
    const { container } = renderPage()
    const h1s = container.querySelectorAll('h1')
    expect(h1s.length).toBe(1)
  })
})

// ── LAND-02 ───────────────────────────────────────────────────────────────────

describe('LAND-02: "Get Started" navigates to /onboarding', () => {
  it('Get Started link has href pointing to /onboarding', () => {
    const { container } = renderPage()
    const link = container.querySelector('#cta-get-started')
    expect(link).not.toBeNull()
    expect(link.getAttribute('href')).toBe('/onboarding')
  })

  it('Get Started is not a div — it is a link or button', () => {
    const { container } = renderPage()
    const link = container.querySelector('#cta-get-started')
    const tagName = link.tagName.toLowerCase()
    expect(['a', 'button']).toContain(tagName)
  })
})

// ── LAND-03 ───────────────────────────────────────────────────────────────────

describe('LAND-03: "Sign In" navigates to /login', () => {
  it('Sign In link has href pointing to /login', () => {
    const { container } = renderPage()
    const link = container.querySelector('#cta-sign-in')
    expect(link).not.toBeNull()
    expect(link.getAttribute('href')).toBe('/login')
  })

  it('Sign In is not a div — it is a link or button', () => {
    const { container } = renderPage()
    const link = container.querySelector('#cta-sign-in')
    const tagName = link.tagName.toLowerCase()
    expect(['a', 'button']).toContain(tagName)
  })
})

// ── LAND-04 ───────────────────────────────────────────────────────────────────

describe('LAND-04: skip link is first focusable element', () => {
  it('first focusable element is the skip-to-main link', () => {
    const { container } = renderPage()

    const focusable = container.querySelectorAll(
      'a[href], button, input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    expect(focusable.length).toBeGreaterThan(0)

    const firstFocusable = focusable[0]
    expect(firstFocusable.getAttribute('href')).toBe('#main-content')
    expect(firstFocusable.textContent.trim()).toBe('Skip to main content')
  })
})

// ── LAND-05 ───────────────────────────────────────────────────────────────────

describe('LAND-05: axe-core scan — 0 critical or serious violations', () => {
  it('has no critical or serious accessibility violations', async () => {
    const { container } = renderPage()

    const results = await axe.run(container, {
      rules: {
        // Disable colour-contrast — jsdom has no computed styles
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
