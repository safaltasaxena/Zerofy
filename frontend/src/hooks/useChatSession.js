/**
 * useChatSession.js — All state and logic for ChatSection.jsx.
 *
 * ARCHITECTURE.md §2.7: max 3 turns per session; bot never uses technical phrases.
 * After turn 3 without resolution → showQuickForm = true.
 * Emoji pre-processing happens before any API call.
 */

import { useState } from 'react'
import { submitChatUpdate } from '../utils/api'

// ── Constants ──────────────────────────────────────────────────────────────────

const MAX_TURNS = 3

const EMOJI_MAP = {
  '🚇': 'metro',
  '🚗': 'petrol_car',
  '🚌': 'bus',
  '🚲': 'cycling',
  '🚶': 'walking',
  '🌱': 'vegan',
  '🍗': 'non_vegetarian',
  '❄️': 'ac_usage',
  '🛵': 'petrol_two_wheeler',
}

const GREETING = "Hi! Tell me about your day — what did you travel by, what did you eat?"

// ── Pure helpers ───────────────────────────────────────────────────────────────

export function preprocessEmoji(text) {
  return Object.entries(EMOJI_MAP).reduce(
    (str, [emoji, word]) => str.replaceAll(emoji, word),
    text
  )
}

function buildDeltaMessage(deltaKg) {
  if (typeof deltaKg !== 'number') return null
  if (deltaKg < 0) return `You saved ${Math.abs(deltaKg).toFixed(2)} kg today 🌱`
  return "A bit higher today — that's okay. Small changes add up."
}

function buildPrefills(parseData, profile) {
  return {
    commute_mode: parseData?.commute_mode || profile?.commute_mode || '',
    avg_daily_km: parseData?.avg_daily_km ?? profile?.avg_daily_km ?? 0,
    ac_hours_per_day: parseData?.ac_hours_per_day ?? profile?.ac_hours_per_day ?? 0,
    diet_type: parseData?.diet_type || profile?.diet_type || '',
  }
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useChatSession({ profile, onUpdateConfirmed }) {
  const [messages, setMessages] = useState([{ text: GREETING, isBot: true }])
  const [turnCount, setTurnCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [showQuickForm, setShowQuickForm] = useState(false)
  const [prefillData, setPrefillData] = useState(null)
  const [pendingData, setPendingData] = useState(null)

  const addMessage = (text, isBot, isError = false) =>
    setMessages((prev) => [...prev, { text, isBot, isError }])

  const handleSend = async (inputText) => {
    const text = inputText.trim()
    if (!text || text.length > 500 || isLoading) return

    const processed = preprocessEmoji(text)
    addMessage(text, false)          // show original emoji text to user
    const newTurn = turnCount + 1
    setTurnCount(newTurn)

    try {
      setIsLoading(true)
      const data = await submitChatUpdate(processed)

      if (data?.confidence === 'high' && newTurn < MAX_TURNS) {
        addMessage(data.bot_reply || "Got it! Does this look right?", true)
        setPreviewData(data.preview)
        setPendingData(data)
        setShowPreview(true)
      } else if (data?.confidence === 'high' && newTurn >= MAX_TURNS) {
        // Turn 3 high confidence — still show form (always rule)
        addMessage(data.bot_reply || "Got it! Does this look right?", true)
        setPreviewData(data.preview)
        setPendingData(data)
        setShowPreview(true)
        setPrefillData(buildPrefills(data, profile))
        setShowQuickForm(true)
      } else {
        const reply = data?.bot_reply || "Could you tell me a little more about that?"
        addMessage(reply, true)
        setPrefillData(buildPrefills(data, profile))

        if (newTurn >= 2) {
          addMessage("Let me show you a quick form — that'll be faster.", true)
          setShowQuickForm(true)
        }
      }
    } catch {
      addMessage("Something went wrong. You can use the form below to update directly.", true, true)
      setPrefillData(buildPrefills(null, profile))
      setShowQuickForm(true)
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirm = () => {
    setShowPreview(false)
    const deltaMsg = buildDeltaMessage(pendingData?.delta_kg ?? null)
    if (deltaMsg) addMessage(deltaMsg, true)
    if (onUpdateConfirmed) onUpdateConfirmed(pendingData)
    setTurnCount(0)
    setPendingData(null)
  }

  const handleEdit = () => {
    setShowPreview(false)
    addMessage("No problem! Tell me what actually happened and I'll try again.", true)
  }

  const handleQuickSubmit = async (formData) => {
    const msg =
      `Updated: ${formData.commute_mode} for ${formData.avg_daily_km} km, ` +
      `${formData.diet_type} diet, ${formData.ac_hours_per_day}h AC`
    try {
      setIsLoading(true)
      const data = await submitChatUpdate(msg)
      setShowQuickForm(false)
      addMessage("Got it — your habits have been updated. 🌿", true)
      const deltaMsg = buildDeltaMessage(data?.delta_kg ?? null)
      if (deltaMsg) addMessage(deltaMsg, true)
      if (onUpdateConfirmed) onUpdateConfirmed(data)
    } catch {
      addMessage("Couldn't save right now — please check your connection and try again.", true, true)
    } finally {
      setIsLoading(false)
    }
  }

  return {
    messages,
    turnCount,
    isLoading,
    showPreview,
    previewData,
    showQuickForm,
    prefillData,
    handleSend,
    handleConfirm,
    handleEdit,
    handleQuickSubmit,
  }
}
