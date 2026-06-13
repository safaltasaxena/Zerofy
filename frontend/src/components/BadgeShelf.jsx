import React from 'react'

const BADGE_MAP = {
  'First Step': { emoji: '🌱', label: 'First Step badge' },
  'Week Warrior': { emoji: '🔥', label: 'Week Warrior badge' },
  'Carbon Cutter': { emoji: '✂️', label: 'Carbon Cutter badge' },
  'Quiz Master': { emoji: '🏆', label: 'Quiz Master badge' },
}

export default function BadgeShelf({ badges }) {
  // Filter badges and map to metadata, ignoring unknown ones safely
  const earnedBadges = (badges || [])
    .filter((badgeId) => Object.prototype.hasOwnProperty.call(BADGE_MAP, badgeId))
    .map((badgeId) => ({
      id: badgeId,
      ...BADGE_MAP[badgeId],
    }))

  const isEmpty = earnedBadges.length === 0

  if (isEmpty) {
    return (
      <div className="text-sm text-gray-400 font-medium py-2">
        No badges yet — keep logging!
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-3" role="list">
      {earnedBadges.map((badge) => (
        <div
          key={badge.id}
          className="flex flex-col items-center justify-center p-3 bg-gray-50 border border-gray-150 rounded-xl min-w-[72px] min-h-[72px] text-center"
          aria-label={badge.label}
          role="listitem"
        >
          <span className="text-2xl mb-1" aria-hidden="true">
            {badge.emoji}
          </span>
          <span className="text-[10px] uppercase tracking-wider font-bold text-gray-500">
            {badge.id}
          </span>
        </div>
      ))}
    </div>
  )
}
