/**
 * SuggestionsList.jsx — 3 personalised suggestion cards with local dismiss.
 *
 * ACCESSIBILITY.md §8: dismiss button has aria-label="Dismiss: [text]".
 * Dismissed state is local — never persisted to API.
 */

import { useState } from 'react'

function SkeletonCard() {
  return (
    <div className="animate-pulse bg-white rounded-xl p-4 flex flex-col gap-2 shadow-sm">
      <div className="h-4 bg-gray-200 rounded w-full" />
      <div className="h-4 bg-gray-200 rounded w-4/5" />
      <div className="h-3 bg-gray-100 rounded w-1/4 self-end mt-1" />
    </div>
  )
}

export default function SuggestionsList({ suggestions, isLoading }) {
  const [dismissed, setDismissed] = useState([])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  const handleDismiss = (index) => {
    setDismissed((prev) => [...prev, index])
  }

  const hasVisible = suggestions.some((_, i) => !dismissed.includes(i))

  if (!suggestions || suggestions.length === 0 || !hasVisible) {
    return (
      <div className="bg-white rounded-xl p-6 text-center text-gray-400 text-sm">
        All caught up! Check back tomorrow for new suggestions.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {suggestions.map((suggestion, i) => {
        const isDismissed = dismissed.includes(i)
        if (isDismissed) return null
        return (
          <div
            key={i}
            className="bg-white rounded-xl p-4 flex items-start justify-between gap-3 shadow-sm"
          >
            <p className="text-sm text-gray-700 leading-relaxed flex-1">{suggestion}</p>
            <button
              onClick={() => handleDismiss(i)}
              aria-label={`Dismiss: ${suggestion}`}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500 rounded flex-shrink-0 min-h-[44px] min-w-[44px] flex items-center justify-center transition-colors duration-200"
            >
              <span aria-hidden="true">✕</span>
            </button>
          </div>
        )
      })}
    </div>
  )
}
