/**
 * useOnboardingForm.js — All state and logic for the onboarding form.
 *
 * Extracted from OnboardingForm.jsx so the component stays under 150 lines
 * and contains zero logic inside JSX.
 *
 * Returns:
 *   fields       — controlled field values
 *   errors       — per-field error strings
 *   networkError — string | null
 *   isLoading    — bool
 *   honeypot     — string (value of the bot-trap input)
 *   handleChange — (e) => void
 *   handleBlur   — (e) => void
 *   handleSubmit — (e) => void
 *   setHoneypot  — (value) => void
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitOnboarding, getProfile } from '../utils/api'

// ── Validation messages — exact text from ACCESSIBILITY.md §7 ─────────────────

const ERRORS = {
  name:                        "What should we call you?",
  state:                       "Please enter your state",
  city:                        "Please enter your city",
  commute_mode:                "Please select your main way of getting around",
  diet_type:                   "Please select the option that best describes how you eat",
  persona:                     "Please select the option that best describes you",
  avg_daily_km_negative:       "Distance can't be negative",
  avg_daily_km_max:            "Enter a distance between 0 and 500 km",
  ac_hours_max:                "AC hours can't be more than 24 in a day",
  electricity_negative:        "Electricity units can't be negative",
  electricity_max:             "Enter a value between 0 and 10,000 units",
  lpg_max:                     "Enter a value between 0 and 10 cylinders",
  network:                     "Couldn't save right now — check your connection and try again",
}

const INITIAL_FIELDS = {
  name: '', state: '', city: '',
  commute_mode: '', avg_daily_km: '',
  diet_type: '', ac_hours_per_day: '',
  monthly_electricity_units: '',
  lpg_cylinders_per_month: '', persona: '',
}

// ── Per-field validation ───────────────────────────────────────────────────────

function validateField(name, value) {
  const str = String(value).trim()
  const num = Number(value)

  if (name === 'name'         && !str)       return ERRORS.name
  if (name === 'state'        && !str)       return ERRORS.state
  if (name === 'city'         && !str)       return ERRORS.city
  if (name === 'commute_mode' && !str)       return ERRORS.commute_mode
  if (name === 'diet_type'    && !str)       return ERRORS.diet_type
  if (name === 'persona'      && !str)       return ERRORS.persona

  if (name === 'avg_daily_km') {
    if (num < 0)   return ERRORS.avg_daily_km_negative
    if (num > 500) return ERRORS.avg_daily_km_max
  }

  if (name === 'ac_hours_per_day' && num > 24)     return ERRORS.ac_hours_max
  if (name === 'monthly_electricity_units') {
    if (num < 0)     return ERRORS.electricity_negative
    if (num > 10000) return ERRORS.electricity_max
  }
  if (name === 'lpg_cylinders_per_month' && num > 10) return ERRORS.lpg_max

  return null
}

// ── Full-form validation ───────────────────────────────────────────────────────

const ALL_FIELDS = [
  'name', 'state', 'city', 'commute_mode', 'avg_daily_km',
  'diet_type', 'ac_hours_per_day', 'monthly_electricity_units',
  'lpg_cylinders_per_month', 'persona',
]

function validateAll(fields) {
  const errs = {}
  ALL_FIELDS.forEach((k) => {
    const e = validateField(k, fields[k])
    if (e) errs[k] = e
  })
  return errs
}

// ── Profile to form fields mapper ─────────────────────────────────────────────

function profileToFields(profile) {
  if (!profile) return INITIAL_FIELDS
  return {
    name:                      profile.name || '',
    state:                     profile.state || '',
    city:                      profile.city || '',
    commute_mode:              profile.commute_mode || '',
    avg_daily_km:              profile.avg_daily_km !== undefined ? String(profile.avg_daily_km) : '',
    diet_type:                 profile.diet_type || '',
    ac_hours_per_day:          profile.ac_hours_per_day !== undefined ? String(profile.ac_hours_per_day) : '',
    monthly_electricity_units: profile.monthly_electricity_units !== undefined ? String(profile.monthly_electricity_units) : '',
    lpg_cylinders_per_month:   profile.lpg_cylinders_per_month !== undefined ? String(profile.lpg_cylinders_per_month) : '',
    persona:                   profile.persona || '',
  }
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useOnboardingForm() {
  const navigate = useNavigate()

  const [fields, setFields]           = useState(INITIAL_FIELDS)
  const [errors, setErrors]           = useState({})
  const [networkError, setNetworkError] = useState(null)
  const [isLoading, setIsLoading]     = useState(false)
  const [honeypot, setHoneypot]       = useState('')
  const [isPrefilling, setIsPrefilling] = useState(true)

  // On mount, try to load existing profile and pre-fill the form.
  // If no profile exists (new user), the form starts blank — that's fine.
  useEffect(() => {
    let cancelled = false
    async function prefillFromProfile() {
      try {
        const profile = await getProfile()
        if (!cancelled && profile) {
          setFields(profileToFields(profile))
        }
      } catch {
        // No existing profile (first-time user) — start with blank form
      } finally {
        if (!cancelled) setIsPrefilling(false)
      }
    }
    prefillFromProfile()
    return () => { cancelled = true }
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFields((prev) => ({ ...prev, [name]: value }))
  }

  const handleBlur = (e) => {
    const { name, value } = e.target
    const err = validateField(name, value)
    setErrors((prev) => ({ ...prev, [name]: err }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (honeypot)  return   // Honeypot filled — silent drop
    if (isLoading) return   // Double-submit guard

    const errs = validateAll(fields)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }

    const payload = {
      name:                       fields.name.trim(),
      state:                      fields.state.trim(),
      city:                       fields.city.trim(),
      commute_mode:               fields.commute_mode,
      avg_daily_km:               Number(fields.avg_daily_km),
      diet_type:                  fields.diet_type,
      ac_hours_per_day:           Number(fields.ac_hours_per_day),
      monthly_electricity_units:  Number(fields.monthly_electricity_units),
      lpg_cylinders_per_month:    Number(fields.lpg_cylinders_per_month),
      persona:                    fields.persona,
    }

    try {
      setIsLoading(true)
      setNetworkError(null)
      await submitOnboarding(payload)
      navigate('/dashboard')
    } catch {
      setNetworkError(ERRORS.network)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    fields,
    errors,
    networkError,
    isLoading: isLoading || isPrefilling,
    honeypot,
    setHoneypot,
    handleChange,
    handleBlur,
    handleSubmit,
  }
}

