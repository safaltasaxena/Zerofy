/**
 * LeaderboardSnippet.jsx — Fetches and shows top 3 for the user's state.
 *
 * This component fetches its own data (per ARCHITECTURE.md §2.4 exception).
 * State name comes from the Dashboard profile prop.
 *
 * EDGE-21: rank 1 displays "1st" — ordinal formatting for all ranks.
 * EDGE-22: if user not in top 3 → "You're not ranked yet — keep logging!"
 */

import { useState, useEffect } from 'react'
import { getLeaderboard } from '../utils/api'

function toOrdinal(n) {
  const mod100 = n % 100
  const mod10  = n % 10
  if (mod100 >= 11 && mod100 <= 13) return `${n}th`
  if (mod10 === 1) return `${n}st`
  if (mod10 === 2) return `${n}nd`
  if (mod10 === 3) return `${n}rd`
  return `${n}th`
}

function SkeletonRow() {
  return (
    <div className="animate-pulse flex items-center gap-3 py-2">
      <div className="w-8 h-4 bg-gray-200 rounded" />
      <div className="flex-1 h-4 bg-gray-200 rounded" />
      <div className="w-14 h-4 bg-gray-200 rounded" />
    </div>
  )
}

export default function LeaderboardSnippet({ state, isLoading: parentLoading }) {
  const [entries, setEntries]         = useState([])
  const [fetchLoading, setFetchLoading] = useState(true)
  const [error, setError]             = useState(null)

  const userId = localStorage.getItem('zerofy_user_id')

  useEffect(() => {
    if (!state) return

    async function fetchLeaderboard() {
      try {
        setFetchLoading(true)
        const data = await getLeaderboard(state)
        setEntries(data?.leaderboard?.slice(0, 3) || [])
      } catch (err) {
        setError('Could not load the leaderboard. Try again later.')
      } finally {
        setFetchLoading(false)
      }
    }

    fetchLeaderboard()
  }, [state])

  const isLoading     = parentLoading || fetchLoading
  const userInTop3    = entries.some((e) => e.user_id === userId)
  const showNoRankMsg = !userInTop3 && entries.length > 0

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl p-4">
        <div className="animate-pulse h-4 bg-gray-200 rounded w-2/5 mb-3" />
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-4 text-center text-sm text-gray-400">
        {error}
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-xl p-4 text-center text-sm text-gray-400">
        No leaderboard data yet for {state || 'your state'}.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Top 3 — {state}
      </h3>

      <ol className="flex flex-col divide-y divide-gray-100">
        {entries.map((entry, idx) => {
          const rank          = idx + 1
          const isCurrentUser = entry.user_id === userId
          const rowCls        = isCurrentUser
            ? 'flex items-center gap-3 py-2 bg-green-50 rounded-lg px-2'
            : 'flex items-center gap-3 py-2 px-2'

          return (
            <li key={entry.user_id || idx} className={rowCls}>
              <span className="w-8 text-sm font-bold text-gray-500 flex-shrink-0">
                {toOrdinal(rank)}
              </span>
              <span className="flex-1 text-sm text-gray-800 font-medium truncate">
                {entry.name}
                {isCurrentUser && (
                  <span className="ml-1 text-xs text-green-600 font-normal">(you)</span>
                )}
              </span>
              <span className="text-sm text-green-700 font-semibold flex-shrink-0">
                {entry.awareness_score} pts
              </span>
            </li>
          )
        })}
      </ol>

      {showNoRankMsg && (
        <p className="text-xs text-gray-400 text-center mt-3">
          You're not ranked yet — keep logging!
        </p>
      )}
    </div>
  )
}
