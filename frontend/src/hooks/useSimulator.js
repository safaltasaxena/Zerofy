/**
 * useSimulator.js — All state and logic for SimulatorSection.jsx.
 *
 * EFFICIENCY.md §3: simulate() is pure and synchronous — no async, no await, zero API calls.
 * EFFICIENCY.md §4: Slider changes debounced at exactly 200ms.
 * Debounce wraps the calculation function — not the state setter.
 * Pending debounce is cancelled on unmount via useEffect cleanup.
 */

import { useState, useEffect, useRef } from 'react'
import { simulate } from '../utils/simulator'

// ── Debounce utility ──────────────────────────────────────────────────────────

function debounce(fn, delay) {
  let timer = null
  const debounced = (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
  debounced.cancel = () => clearTimeout(timer)
  return debounced
}

// ── Natural language builder ──────────────────────────────────────────────────

const MODE_LABELS = {
  petrol_car: 'a petrol car',
  diesel_car: 'a diesel car',
  petrol_two_wheeler: 'a petrol two-wheeler',
  electric_vehicle: 'an electric vehicle',
  auto_rickshaw: 'an auto rickshaw',
  bus: 'the bus',
  metro: 'the metro',
  walking: 'walking',
  cycling: 'cycling',
}

export function buildLogMessage(sliderState, profile) {
  const parts = []

  if (sliderState.commute_mode !== profile?.commute_mode || sliderState.avg_daily_km !== profile?.avg_daily_km) {
    const modeLabel = MODE_LABELS[sliderState.commute_mode] || sliderState.commute_mode
    parts.push(`I switched to ${modeLabel} for ${sliderState.avg_daily_km} km today`)
  }
  if (sliderState.diet_type !== profile?.diet_type) {
    parts.push(`I ate ${sliderState.diet_type} today`)
  }
  if (sliderState.ac_hours_per_day !== profile?.ac_hours_per_day) {
    parts.push(`I used AC for ${sliderState.ac_hours_per_day} hours`)
  }
  if (sliderState.lpg_cylinders_per_month !== profile?.lpg_cylinders_per_month) {
    parts.push(`my LPG usage is about ${sliderState.lpg_cylinders_per_month} cylinders per month`)
  }

  return parts.length > 0 ? parts.join(', ') + '.' : 'No changes from my usual habits.'
}

// ── Safe simulate wrapper ─────────────────────────────────────────────────────

const EMPTY_BREAKDOWN = { transport: 0, diet: 0, electricity: 0, lpg: 0, total: 0 }

function safeSimulate(params) {
  try {
    const result = simulate(params)
    return { ...result.breakdown }
  } catch {
    return EMPTY_BREAKDOWN
  }
}

// ── Hook ──────────────────────────────────────────────────────────────────────

function buildInitialState(profile) {
  return {
    commute_mode: profile?.commute_mode || 'bus',
    avg_daily_km: profile?.avg_daily_km ?? 10,
    diet_type: profile?.diet_type || 'vegetarian',
    ac_hours_per_day: profile?.ac_hours_per_day ?? 2,
    monthly_electricity_units: profile?.monthly_electricity_units ?? 150,
    lpg_cylinders_per_month: profile?.lpg_cylinders_per_month ?? 1,
  }
}

export function useSimulator({ profile }) {
  const [sliderState, setSliderState] = useState(() => buildInitialState(profile))
  const [breakdown, setBreakdown] = useState(() => safeSimulate(buildInitialState(profile)))
  const [isLoading, setIsLoading] = useState(false)

  const recalculate = (params) => {
    setIsLoading(true)
    const result = safeSimulate(params)
    setBreakdown(result)
    setIsLoading(false)
  }

  const debouncedRef = useRef(null)
  const isFirstRender = useRef(true)

  useEffect(() => {
    debouncedRef.current = debounce(recalculate, 200)
    return () => debouncedRef.current?.cancel()
  }, [])

  // Cancel pending debounce on unmount
  useEffect(() => {
    const debounced = debouncedRef.current
    return () => debounced?.cancel()
  }, [])

  // FIX 2: Sync sliders when profile loads async after initial mount
  useEffect(() => {
    if (profile) {
      const initial = buildInitialState(profile)
      setSliderState(initial)
      if (isFirstRender.current) {
        isFirstRender.current = false
      } else {
        recalculate(initial)
      }
    }
  }, [profile])

  const handleSliderChange = (field, value) => {
    const next = { ...sliderState, [field]: (field === "commute_mode" || field === "diet_type") ? value : Number(value) }
    setSliderState(next)
    debouncedRef.current?.(next)
  }

  return { sliderState, breakdown, isLoading, handleSliderChange, buildLogMessage }
}
