import React from 'react'

export default function QuestionCard({
  question,
  options,
  selectedIndex,
  onSelect,
  questionNumber,
  totalQuestions,
  isSubmitted = false,
}) {
  const { question: questionText } = question

  // Pre-calculate button classes to avoid logic inside JSX return
  const buttonStyles = options.map((option, idx) => {
    const isSelected = selectedIndex === idx
    const isCorrect = question.correct_index === idx

    if (isSubmitted) {
      if (isCorrect) {
        return 'w-full text-left px-4 py-3 rounded-xl border-2 border-green-600 bg-green-50 text-green-950 font-semibold min-h-[44px] transition-all'
      }
      if (isSelected) {
        return 'w-full text-left px-4 py-3 rounded-xl border-2 border-red-500 bg-red-50 text-red-950 font-medium min-h-[44px] transition-all'
      }
      return 'w-full text-left px-4 py-3 rounded-xl border-2 border-gray-100 bg-gray-50/50 text-gray-400 cursor-not-allowed min-h-[44px]'
    }

    if (isSelected) {
      return 'w-full text-left px-4 py-3 rounded-xl border-2 border-green-500 bg-green-50 text-green-950 font-semibold min-h-[44px] focus:outline-none focus:ring-2 focus:ring-green-500 transition-all'
    }

    return 'w-full text-left px-4 py-3 rounded-xl border-2 border-gray-200 hover:border-green-300 hover:bg-green-50/20 text-gray-700 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-green-500 transition-all'
  })

  const progressText = `Question ${questionNumber} of ${totalQuestions}`

  const handleKeyDown = (e, index) => {
    if (e.key === ' ' || e.key === 'Spacebar') {
      e.preventDefault()
      onSelect(index)
    }
  }

  return (
    <div className="w-full bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col gap-4">
      <div className="text-sm font-semibold text-green-600 tracking-wide uppercase">
        {progressText}
      </div>
      <h2 className="text-lg font-bold text-gray-900 leading-snug">
        {questionText}
      </h2>
      <div className="flex flex-col gap-3 mt-2">
        {options.map((option, idx) => {
          const isSelected = selectedIndex === idx
          const styles = buttonStyles[idx]
          const handleOptionClick = () => {
            if (!isSubmitted) {
              onSelect(idx)
            }
          }

          return (
            <button
              key={idx}
              type="button"
              className={styles}
              onClick={handleOptionClick}
              onKeyDown={e => handleKeyDown(e, idx)}
              disabled={isSubmitted}
              aria-pressed={isSelected}
            >
              {option}
            </button>
          )
        })}
      </div>
    </div>
  )
}
