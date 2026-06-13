/**
 * Dashboard.jsx — Main scrolling dashboard page for Zerofy India.
 *
 * EFFICIENCY.md §7: 4 parallel calls via Promise.all on mount.
 * ARCHITECTURE.md §2.8: userId from localStorage("zerofy_user_id") — display-only, not token.
 * ACCESSIBILITY.md §8: semantic <nav>, <main>, <section>, <h2> per section.
 * Smooth scroll with prefers-reduced-motion check per ACCESSIBILITY.md §10.
 */

import { useState, useEffect } from 'react'
import { getProfile, getTodayLog, getGamification, getWeeklyTrend } from '../utils/api'

import ScoreBreakdown from '../components/ScoreBreakdown'
import SuggestionsList from '../components/SuggestionsList'
import StreakCounter from '../components/StreakCounter'
import WeeklyChart from '../components/WeeklyChart'
import LeaderboardSnippet from '../components/LeaderboardSnippet'
import SimulatorSection from '../components/SimulatorSection'

const NAV_LINKS = [
  { label: 'Score', href: '#score' },
  { label: 'Suggestions', href: '#suggestions' },
  { label: 'Chat', href: '#chat' },
  { label: 'Simulator', href: '#simulator' },
  { label: 'Streak', href: '#streak' },
]

const EMPTY_BREAKDOWN = { transport: 0, diet: 0, electricity: 0, lpg: 0, total: 0 }

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [todayLog, setTodayLog] = useState(null)
  const [gamification, setGamification] = useState(null)
  const [trend, setTrend] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [chatPrefill, setChatPrefill] = useState('')

  useEffect(() => {
    const userId = localStorage.getItem('zerofy_user_id')

    async function fetchDashboard() {
      try {
        setIsLoading(true)
        // EFFICIENCY.md §7: exactly 3 parallel calls on dashboard mount
        const [profileData, logData, gamData] = await Promise.all([
          getProfile(),
          getTodayLog(userId),
          getGamification(userId),
        ])
        setProfile(profileData)
        setTodayLog(logData)
        setGamification(gamData)

        // Weekly trend fetched separately after the 3-call budget resolves
        try {
          const trendData = await getWeeklyTrend(userId)
          setTrend(trendData?.logs || [])
        } catch {
          // Non-critical — chart shows empty state if this fails
          setTrend([])
        }
      } catch (err) {
        setError(err.message || 'Could not load your dashboard. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  const handleNavClick = (e, href) => {
    e.preventDefault()
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const target = document.querySelector(href)
    if (target) target.scrollIntoView({ behavior: prefersReduced ? 'auto' : 'smooth' })
  }

  const handleLogChanges = (message) => {
    setChatPrefill(message)
  }

  const breakdown = todayLog?.breakdown || EMPTY_BREAKDOWN
  const analogy = todayLog?.analogy || ''
  const suggestions = todayLog?.suggestions || []
  const streak = gamification?.log_streak ?? 0
  const points = gamification?.awareness_score ?? 0
  const badges = gamification?.badges || []
  const userState = profile?.state || ''

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div role="alert" className="text-center">
          <p className="text-red-700 text-base mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-semibold min-h-[44px]"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav aria-label="Dashboard sections" className="sticky top-0 z-10 bg-white border-b border-gray-200 px-4 py-2">
        <ul className="flex gap-4 justify-end overflow-x-auto text-sm font-medium">
          {NAV_LINKS.map(({ label, href }) => (
            <li key={href}>
              <a
                href={href}
                onClick={(e) => handleNavClick(e, href)}
                className="text-green-700 hover:text-green-900 focus:outline-none focus:ring-2 focus:ring-green-500 rounded whitespace-nowrap"
              >
                {label}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <main id="main-content" className="max-w-lg mx-auto px-4 py-6 flex flex-col gap-8">
        <section id="score" aria-labelledby="score-heading">
          <h2 id="score-heading" className="text-lg font-bold text-gray-800 mb-3">Today's Score</h2>
          <ScoreBreakdown breakdown={breakdown} analogy={analogy} isLoading={isLoading} />
        </section>

        <section id="suggestions" aria-labelledby="suggestions-heading">
          <h2 id="suggestions-heading" className="text-lg font-bold text-gray-800 mb-3">Suggestions</h2>
          <SuggestionsList suggestions={suggestions} isLoading={isLoading} />
        </section>

        <section id="chat" aria-labelledby="chat-heading">
          <h2 id="chat-heading" className="text-lg font-bold text-gray-800 mb-3">Chat</h2>
          <div id="chat" data-prefill={chatPrefill} className="bg-white rounded-xl p-6 text-center text-gray-400 border border-dashed border-gray-300">
            Chat coming in Phase 12
          </div>
        </section>

        <section id="simulator" aria-labelledby="simulator-heading">
          <h2 id="simulator-heading" className="text-lg font-bold text-gray-800 mb-3">Simulator</h2>
          <SimulatorSection
            profile={profile}
            onLogChanges={handleLogChanges}
          />
        </section>

        <section id="streak" aria-labelledby="streak-heading">
          <h2 id="streak-heading" className="text-lg font-bold text-gray-800 mb-3">Your Progress</h2>
          <div className="flex flex-col gap-4">
            <StreakCounter streak={streak} points={points} badges={badges} isLoading={isLoading} />
            <WeeklyChart trend={trend} isLoading={isLoading} />
            <LeaderboardSnippet state={userState} isLoading={isLoading} />
          </div>
        </section>
      </main>
    </div>
  )
}
