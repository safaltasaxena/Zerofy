import React from 'react'

export default function ResultCard({ score, totalQuestions, pointsEarned, correctAnswers }) {
  // Pre-calculate message to keep JSX return free of logic
  let encouragement = ''
  if (score === 3) {
    encouragement = "Perfect score! 🏆 You're a carbon expert"
  } else if (score === 2) {
    encouragement = "Great job! 🌱 Keep learning"
  } else if (score === 1) {
    encouragement = "Good start! Every point counts 💪"
  } else {
    encouragement = 'Keep going — knowledge grows with practice'
  }

  const scoreText = `You got ${score} out of ${totalQuestions}`
  const pointsText = `+${pointsEarned} Points`

  return (
    <div
      className="w-full bg-green-50/50 border border-green-100 rounded-2xl p-6 shadow-sm flex flex-col items-center text-center gap-4"
      aria-live="polite"
    >
      <div className="text-4xl">🎯</div>
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-1">
          {scoreText}
        </h2>
        <p className="text-green-700 font-extrabold text-2xl tracking-wide">
          {pointsText}
        </p>
      </div>
      <p className="text-gray-700 font-medium max-w-sm">
        {encouragement}
      </p>
    </div>
  )
}
