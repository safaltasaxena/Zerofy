import React, { useState, useEffect } from 'react'
import { getTodayQuiz, submitQuizAnswers } from '../utils/api'
import QuestionCard from '../components/QuestionCard'
import ResultCard from '../components/ResultCard'

export default function DailyQuiz() {
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState([null, null, null])
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [isLocked, setIsLocked] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [quizResult, setQuizResult] = useState(null)

  const userId = localStorage.getItem('zerofy_user_id')

  useEffect(() => {
    async function loadQuiz() {
      try {
        setLoading(true)
        setError(null)
        const data = await getTodayQuiz(userId)
        if (data?.submitted === true) {
          setIsLocked(true)
        } else {
          setQuestions(data?.questions || [])
        }
      } catch (err) {
        setError(err.message || 'Failed to load quiz.')
      } finally {
        setLoading(false)
      }
    }
    loadQuiz()
  }, [userId])

  const handleSelectOption = (optionIndex) => {
    setSelectedAnswers((prev) => {
      const next = [...prev]
      next[currentStep] = optionIndex
      return next
    })
  }

  const handleNext = () => {
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleSubmit = async () => {
    if (submitting) return
    try {
      setSubmitting(true)
      setError(null)
      
      // Score calculation comparing selected answer against correct index (FIX 3)
      const score = selectedAnswers.reduce((acc, ans, i) => {
        const match = ans === questions[i].correct_index
        return acc + (match ? 1 : 0)
      }, 0)
      const points = score * 5

      await submitQuizAnswers(selectedAnswers)
      
      setQuizResult({
        score,
        pointsEarned: points,
      })
      setIsSubmitted(true)
    } catch (err) {
      setError(err.message || 'Failed to submit quiz.')
    } finally {
      setSubmitting(false)
    }
  }

  // Pre-calculated values to keep logic out of JSX
  const currentAnswer = selectedAnswers[currentStep]
  const isLastQuestion = currentStep === 2
  const currentQuestion = questions[currentStep]
  const isNextDisabled = currentAnswer === null
  const isSubmitDisabled = currentAnswer === null || submitting

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6" aria-busy="true">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Daily Quiz</h1>
        <div className="text-gray-500 animate-pulse">Loading quiz questions...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Daily Quiz</h1>
        <div className="text-red-600 bg-red-50 px-4 py-3 rounded-xl border border-red-150 max-w-md text-center" role="alert">
          {error}
        </div>
      </div>
    )
  }

  if (isLocked) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Daily Quiz</h1>
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-150 max-w-md text-center">
          <p className="text-gray-700 font-medium leading-relaxed">
            You&apos;ve already completed today&apos;s quiz 🎯
            <br />
            Come back tomorrow for a new one!
          </p>
        </div>
      </div>
    )
  }

  if (isSubmitted && quizResult) {
    const isCorrectArr = selectedAnswers.map((ans, i) => ans === questions[i].correct_index)
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Daily Quiz</h1>
        <div className="w-full max-w-md flex flex-col gap-4">
          <ResultCard
            score={quizResult.score}
            totalQuestions={3}
            pointsEarned={quizResult.pointsEarned}
            correctAnswers={isCorrectArr}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Daily Quiz</h1>
      <div className="w-full max-w-md flex flex-col gap-4">
        {currentQuestion && (
          <QuestionCard
            question={currentQuestion}
            options={currentQuestion.options}
            selectedIndex={currentAnswer}
            onSelect={handleSelectOption}
            questionNumber={currentStep + 1}
            totalQuestions={3}
          />
        )}
        <div className="flex justify-end mt-2">
          {isLastQuestion ? (
            <button
              type="button"
              className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl min-h-[44px] min-w-[120px] transition-colors"
              onClick={handleSubmit}
              disabled={isSubmitDisabled}
            >
              {submitting ? 'Submitting...' : 'Submit'}
            </button>
          ) : (
            <button
              type="button"
              className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl min-h-[44px] min-w-[120px] transition-colors"
              onClick={handleNext}
              disabled={isNextDisabled}
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
