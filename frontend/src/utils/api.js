/**
 * api.js — All HTTP calls to the Zerofy India backend go through this module.
 *
 * CODING_STANDARDS.md §2.6: Components never use fetch() or axios directly.
 * CODING_STANDARDS.md §2: api.js must stay under 200 lines.
 *
 * Token source: localStorage key "zerofy_token" — set on login, cleared on logout.
 * The request interceptor attaches it automatically to every call.
 */

import axios from 'axios'

// ── Axios instance — baseURL from env, no hardcoded URLs ─────────────────────

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor — attach token to every call ─────────────────────────

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('zerofy_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (err) => Promise.reject(err)
)

// ── Response helper — unwrap data.data, throw on API-level failure ────────────

function unwrap(response) {
  if (!response.data.success) {
    throw new Error(response.data.error || 'Request failed')
  }
  return response.data.data
}

// ── Auth ──────────────────────────────────────────────────────────────────────

/** Sign in with email + password. Returns Firebase credential data. */
export async function loginUser(email, password) {
  try {
    const res = await api.post('/api/auth/login', { email, password })
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Register a new user. */
export async function signupUser(email, password, name) {
  try {
    const res = await api.post('/api/auth/signup', { email, password, name })
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Clear the stored token and sign out on the backend. */
export async function logoutUser() {
  try {
    localStorage.removeItem('zerofy_token')
    const res = await api.post('/api/auth/logout')
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

// ── User ──────────────────────────────────────────────────────────────────────

/** Fetch the authenticated user's profile. */
export async function getProfile() {
  try {
    const res = await api.get('/api/user/profile')
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Submit partial profile update fields. */
export async function updateProfile(profileData) {
  try {
    const res = await api.put('/api/user/profile', profileData)
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Submit onboarding form data. */
export async function submitOnboarding(onboardingData) {
  try {
    const res = await api.post('/api/user/onboarding', onboardingData)
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

// ── Logs ──────────────────────────────────────────────────────────────────────

/** Fetch today's log for a user. */
export async function getTodayLog(userId) {
  try {
    const res = await api.get(`/api/logs/${userId}/today`)
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Fetch the last 7 days of CO2 trend data. */
export async function getWeeklyTrend(userId) {
  try {
    const res = await api.get(`/api/logs/${userId}/weekly`)
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Submit a natural language chat message for NLP parsing and log update. */
export async function submitChatUpdate(message) {
  try {
    const res = await api.post('/api/logs/chat-update', { message })
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

// ── Quiz ──────────────────────────────────────────────────────────────────────

/** Fetch today's quiz questions (cached or freshly generated). */
export async function getTodayQuiz(userId) {
  try {
    const res = await api.get(`/api/quiz/today/${userId}`)
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

/** Submit quiz answers (array of 3 indices). */
export async function submitQuizAnswers(answers) {
  try {
    const res = await api.post('/api/quiz/submit', { answers })
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

// ── Gamification ──────────────────────────────────────────────────────────────

/** Fetch gamification state (streak, points, badges, weekly_score, rank). */
export async function getGamification(userId) {
  try {
    const res = await api.get(`/api/gamification/${userId}`)
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

// ── Leaderboard ───────────────────────────────────────────────────────────────

/** Fetch the state leaderboard for a given Indian state. */
export async function getLeaderboard(state) {
  try {
    const res = await api.get('/api/leaderboard', { params: { state } })
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** Fetch the full emission constants object from the backend. */
export async function fetchConstants() {
  try {
    const res = await api.get('/api/constants')
    return unwrap(res)
  } catch (err) {
    throw new Error(err.response?.data?.error || err.message)
  }
}

export default api
