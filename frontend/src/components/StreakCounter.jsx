/**
 * StreakCounter.jsx — Shows current logging streak, points, and badges.
 *
 * ACCESSIBILITY.md §8: fire emoji 🔥 has aria-hidden="true".
 * aria-label on container: "Current logging streak: X days".
 * If streak === 0 → encouraging message per ACCESSIBILITY.md §6 tone rules.
 */

function SkeletonStreak() {
  return (
    <div className="animate-pulse bg-white rounded-xl p-4 flex gap-4 items-center">
      <div className="w-16 h-16 bg-gray-200 rounded-full flex-shrink-0" />
      <div className="flex flex-col gap-2 flex-1">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-3 bg-gray-200 rounded w-1/2" />
      </div>
    </div>
  )
}

export default function StreakCounter({ streak, points, badges, isLoading }) {
  if (isLoading) return <SkeletonStreak />

  const isZeroStreak  = streak === 0
  const streakLabel   = `Current logging streak: ${streak} days`
  const hasBadges     = Array.isArray(badges) && badges.length > 0

  return (
    <div className="bg-white rounded-xl p-4">
      <div
        aria-label={streakLabel}
        className="flex items-center gap-3 mb-3"
      >
        <div className="flex items-center gap-1">
          <span className="text-4xl font-bold text-gray-800">{streak}</span>
          <span aria-hidden="true" className="text-3xl leading-none">🔥</span>
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-700">day streak</p>
          <p className="text-xs text-gray-500">{points} points earned</p>
        </div>
      </div>

      {isZeroStreak && (
        <p className="text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
          Log today to keep your streak alive{' '}
          <span aria-hidden="true">🔥</span>
        </p>
      )}

      {hasBadges && (
        <div className="mt-3 flex flex-wrap gap-2">
          {badges.map((badge) => (
            <span
              key={badge}
              aria-label={`${badge} badge`}
              className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium"
            >
              {badge}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
