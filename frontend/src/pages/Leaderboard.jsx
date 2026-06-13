import React, { useState, useEffect } from 'react'
import { getLeaderboard } from '../utils/api'

function toOrdinal(n) {
  const mod100 = n % 100
  const mod10 = n % 10
  if (mod100 >= 11 && mod100 <= 13) return `${n}th`
  if (mod10 === 1) return `${n}st`
  if (mod10 === 2) return `${n}nd`
  if (mod10 === 3) return `${n}rd`
  return `${n}th`
}

const BADGE_MAP = {
  'First Step': '🌱',
  'Week Warrior': '🔥',
  'Carbon Cutter': '✂️',
  'Quiz Master': '🏆',
}

export default function Leaderboard() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const userId = localStorage.getItem('zerofy_user_id')
  const state = localStorage.getItem('zerofy_state')

  useEffect(() => {
    if (!state) {
      setError('Could not load leaderboard. Please update your profile first.')
      setLoading(false)
      return
    }

    async function fetchLeaderboardData() {
      try {
        setLoading(true)
        setError(null)
        const data = await getLeaderboard(state)
        setEntries(data?.leaderboard || [])
      } catch (err) {
        setError(err.message || 'Could not load leaderboard.')
      } finally {
        setLoading(false)
      }
    }

    fetchLeaderboardData()
  }, [state])

  // Derive all data outside JSX
  const userInList = entries.some((e) => e.user_id === userId)
  const showNoRankMessage = !userInList && entries.length > 0
  const skeletonRows = Array.from({ length: 5 })

  if (loading) {
    return (
      <div className="flex flex-col items-center min-h-screen bg-gray-50 p-6" aria-busy="true">
        <div className="w-full max-w-xl flex flex-col gap-4">
          <h1 className="text-2xl font-bold text-gray-900 self-start">Leaderboard</h1>
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-150 flex flex-col gap-3">
            {skeletonRows.map((_, i) => (
              <div key={i} className="animate-pulse flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-5 bg-gray-200 rounded" />
                  <div className="w-24 h-5 bg-gray-200 rounded" />
                </div>
                <div className="w-16 h-5 bg-gray-200 rounded" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Leaderboard</h1>
        <div className="text-red-600 bg-red-50 px-4 py-3 rounded-xl border border-red-150 max-w-md text-center" role="alert">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-50 p-6">
      <div className="w-full max-w-xl flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold text-gray-900">Leaderboard</h1>
          <p className="text-sm text-gray-500 font-medium">Top players in {state}</p>
        </div>

        <div
          className="bg-white rounded-2xl p-4 shadow-sm border border-gray-150 flex flex-col overflow-hidden"
        >
          {entries.length === 0 ? (
            <div className="text-center py-8 text-gray-400 font-medium">
              No ranks available for {state} yet.
            </div>
          ) : (
            <table className="w-full text-left border-collapse" aria-label="State leaderboard">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="py-3 px-2 text-xs font-bold text-gray-400 uppercase tracking-wider w-16">Rank</th>
                  <th className="py-3 px-2 text-xs font-bold text-gray-400 uppercase tracking-wider">Name</th>
                  <th className="py-3 px-2 text-xs font-bold text-gray-400 uppercase tracking-wider text-right w-28">Score</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry, idx) => {
                  const rank = idx + 1
                  const isCurrentUser = entry.user_id === userId
                  const firstName = entry.name ? entry.name.split(' ')[0] : 'User'
                  const badgeIcon = BADGE_MAP[entry.top_badge]
                  const rowClass = isCurrentUser
                    ? 'bg-green-50/70 border-y border-green-100 font-medium text-gray-950 transition-colors'
                    : 'border-b border-gray-50 hover:bg-gray-50/50 transition-colors'

                  return (
                    <tr
                      key={entry.user_id || idx}
                      className={rowClass}
                      aria-current={isCurrentUser ? 'true' : undefined}
                    >
                      <td className="py-3 px-2 text-sm font-bold text-gray-500">
                        {toOrdinal(rank)}
                      </td>
                      <td className="py-3 px-2 text-sm text-gray-800 truncate">
                        <div className="flex items-center gap-2">
                          <span>{firstName}</span>
                          {badgeIcon && (
                            <span role="img" aria-label={`${entry.top_badge} badge`} className="text-base">
                              {badgeIcon}
                            </span>
                          )}
                          {isCurrentUser && (
                            <span className="text-[10px] bg-green-100 text-green-700 font-semibold px-2 py-0.5 rounded-full">
                              You
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-2 text-sm text-green-700 font-bold text-right">
                        {entry.awareness_score} pts
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {showNoRankMessage && (
          <div className="text-center py-2">
            <p className="text-sm text-gray-500 font-semibold">
              You&apos;re not ranked yet — keep logging!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
