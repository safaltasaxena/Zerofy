/**
 * LandingPage.jsx — Static marketing page for Zerofy India.
 *
 * ACCESSIBILITY.md §5: min 360px, 44×44px targets, 16px font, full-width CTAs on mobile.
 * ACCESSIBILITY.md §8: <main>, <header>, one <h1>, skip-to-main link as first tab stop.
 * CODING_STANDARDS.md §2: Tailwind standard utilities only — no custom animations or keyframes.
 */

import { Link } from 'react-router-dom'

const SUBHEADLINE =
  'Log your daily habits in plain English, get your carbon score, and take small actions that actually add up — built for how India travels, eats, and lives.'

export default function LandingPage() {
  return (
    <>
      {/* Skip-to-main — first focusable element per ACCESSIBILITY.md §9 */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-green-700 focus:font-semibold focus:rounded-lg focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-green-600"
      >
        Skip to main content
      </a>

      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex flex-col">
        <header className="w-full px-4 py-4 max-w-lg mx-auto">
          <span
            aria-label="Zerofy India — carbon footprint tracker"
            className="text-green-700 font-bold text-xl tracking-tight"
          >
            🌿 Zerofy
          </span>
        </header>

        <main
          id="main-content"
          className="flex-1 flex flex-col items-center justify-center px-4 py-12 text-center max-w-lg mx-auto w-full"
          tabIndex="-1"
        >
          <section aria-labelledby="hero-heading">
            <h1
              id="hero-heading"
              className="text-3xl font-extrabold text-gray-800 leading-tight mb-4"
            >
              Track your carbon footprint,{' '}
              <span className="text-green-600">Indian style</span>
            </h1>

            <p className="text-base text-gray-600 leading-relaxed mb-10 max-w-sm mx-auto">
              {SUBHEADLINE}
            </p>

            <div className="flex flex-col gap-4 w-full">
              <Link
                to="/onboarding"
                id="cta-get-started"
                className="block w-full py-3 px-6 text-base font-semibold text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 rounded-xl min-h-[44px] text-center transition-colors duration-200"
              >
                Get Started
              </Link>

              <Link
                to="/login"
                id="cta-sign-in"
                className="block w-full py-3 px-6 text-base font-semibold text-green-700 bg-white border-2 border-green-600 hover:bg-green-50 focus:outline-none focus:ring-2 focus:ring-green-600 focus:ring-offset-2 rounded-xl min-h-[44px] text-center transition-colors duration-200"
              >
                Sign In
              </Link>
            </div>
          </section>

          <p className="mt-12 text-sm text-gray-500">
            Takes 2 minutes — no account required to see your score
          </p>
        </main>
      </div>
    </>
  )
}
