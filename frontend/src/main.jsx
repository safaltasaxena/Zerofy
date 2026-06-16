import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import OnboardingForm from './pages/OnboardingForm'
import Dashboard from './pages/Dashboard'
import DailyQuiz from './pages/DailyQuiz'
import Leaderboard from './pages/Leaderboard'
import Profile from './pages/Profile'
import './index.css'
import { loadConstants } from './utils/constants'

// A simple utility to set up unique mock credentials for local testing
const token = localStorage.getItem('zerofy_token')
if (!token) {
  const newId = 'user_' + Math.random().toString(36).substring(2, 11)
  localStorage.setItem('zerofy_token', newId)
  localStorage.setItem('zerofy_user_id', newId)
} else if (!token.includes('.')) {
  // Sync user ID with the token for mock/local development tokens to prevent mismatch
  localStorage.setItem('zerofy_user_id', token)
}

// Load constants on app start
loadConstants().catch(err => console.error("Failed to load constants:", err))

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<OnboardingForm />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/quiz" element={<DailyQuiz />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
