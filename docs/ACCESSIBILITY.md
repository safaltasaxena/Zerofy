# Zerofy India — Accessibility Specification
**Stack:** React + FastAPI | **Standard:** WCAG 2.1 Level AA | **Version:** 1.1
**Used for:** Frontend prompts — ensures UI is built for Indian users, not Silicon Valley defaults.

---

## Core Principles

> **Mobile-first, always.** Most Indian users are on a phone, one-handed, on a slow connection.
> **Plain language, no jargon.** If a 14-year-old in Nagpur can't read it — rewrite it.
> **Fallback always exists.** If AI fails, the form is right there. No dead ends.
> **Persona-aware UI.** A senior citizen and a college student should never feel lost on the same screen.
> **Conversational chat.** The bot speaks like a person — not a command-line interface.

---

## 1. India-Specific UX Considerations

### Device & Network Reality

| Constraint | Rule |
|---|---|
| Mid-range Android phones | All layouts tested at 360px minimum width |
| Slow / intermittent 3G/4G | Every API call shows loading state — never blank screen |
| Limited data plans | No auto-playing video, no large background images |
| One-handed thumb use | Primary actions at bottom of screen or large central buttons |
| Unicode input common | Input fields must accept Unicode — never ASCII-only validation |
| Users type in mixed Hindi/English | Chat input must not reject non-ASCII characters |

### Cultural Defaults

| Context | Rule |
|---|---|
| Units | Always km, always kg — never miles or tonnes |
| Commute options | Auto-rickshaw, metro, BEST bus, two-wheeler are first-class — not edge cases |
| Diet | Eggetarian is a real category — never collapse into vegetarian |
| Fuel | LPG cylinders — not "gas usage" |
| Tone | Warm and encouraging — never clinical or preachy |
| Emojis | Used sparingly for warmth (🔥 streak, 🌱 badge) — not decoration on every element |

---

## 2. Persona-Based UI Adaptation

`persona` field from onboarding drives all dynamic text and suggestion framing.

### Persona Adaptation Matrix

| Persona | Greeting tone | Suggestion framing | Quiz context |
|---|---|---|---|
| `student` | Casual — "Hey Aryan 👋" | Hostel, campus, canteen, pocket money | Campus appliances, auto vs walk |
| `professional` | Efficient — "Good morning, Priya" | Commute, WFH, office energy, carpooling | Office commute, workstation, AC |
| `family` | Warm — "Hello, Ramesh" | Home appliances, cooking, family car | Washing machine, cooking gas, ACs |
| `teenager` | Upbeat — "What's up, Dev 🔥" | School commute, food choices, screen time | School commute, phone charging |
| `senior` | Respectful — "Namaste, Mrs. Mehta" | Home cooling, local travel, cooking | Home cooling, LPG, local transport |

### Persona Rules

- ✅ Set once at onboarding — never ask again unless user re-fills the form
- ✅ Suggestions filtered to only include habits relevant to that persona
- ✅ Quiz questions tagged by persona — only matching tags served
- ✅ Missing persona → default to `professional` (most neutral)
- ❌ Never show student suggestions to a senior
- ❌ Never assume all users have a car — two-wheeler and transit are the majority case

### Commute Mode Visibility by Persona

| Mode | Student | Professional | Family | Teenager | Senior |
|---|---|---|---|---|---|
| Walking / Cycling | ✅ Prominent | ✅ | ✅ | ✅ Prominent | ✅ |
| Two-wheeler (petrol) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Auto-rickshaw | ✅ | ✅ | ✅ | ✅ | ✅ Prominent |
| Bus / Metro | ✅ Prominent | ✅ Prominent | ✅ | ✅ Prominent | ✅ |
| Petrol Car | ✅ | ✅ | ✅ Prominent | — | ✅ |
| Diesel Car | — | ✅ | ✅ Prominent | — | ✅ |
| Electric Vehicle | ✅ | ✅ | ✅ | ✅ | — |
| WFH | — | ✅ Prominent | ✅ | — | — |

---

## 3. Fallback Behaviour — When NLP Fails

### Fallback Decision Flow

```
User submits chat message
        ↓
Emoji pre-processing (🚇 → "metro" etc.)
        ↓
Gemini returns confidence level
        ↓
confidence == "high"?
  YES → ParsePreview badge shown
        Bot says naturally: "Got it — you switched to metro for 8 km 🚇 Confirm?"
  NO + 1st turn → Bot asks ONE follow-up question naturally
  NO + 2nd turn → QuickUpdateForm with pre-filled guesses
```

### Fallback UI Rules

| Scenario | What the UI Must Show |
|---|---|
| Low confidence parse | `QuickUpdateForm` with pre-filled guesses — not blank form |
| Gemini timeout / error | "Hmm, let me show you a quick form instead" + form |
| 3 turns without resolution | `QuickUpdateForm` automatically — no 4th bot turn |
| "Update via form" clicked | `QuickUpdateForm` immediately — no loading |
| Parse preview shown | Clear [Confirm ✅] and [Edit ✏️] buttons |

### Chat Bot Tone Rules

| ❌ Never say | ✅ Say instead |
|---|---|
| "I have parsed your input" | "Got it — switching to metro today?" |
| "Parse failed" | "Hmm, I didn't quite catch that — try the quick form below" |
| "Your confidence score is low" | "Could you tell me a bit more?" |
| "Processing your request" | "Saving your update..." |
| "Invalid entity detected" | "I'm not sure what you mean — could you say it differently?" |

### ParsePreview Badge — Required Elements

```
[Transport → Metro  |  Distance: 8 km]   [Confirm ✅]  [Edit ✏️]
```

| Element | Rule |
|---|---|
| Category | Always shown |
| Change | Old → New value |
| Quantity + unit | Always with unit ("8 km", "2 hours") |
| Confirm button | Primary style — min 44×44px |
| Edit button | Secondary — does not look like dismiss |
| Screen reader | `aria-label="Confirm: Switch to Metro, 8 km"` |

### QuickUpdateForm Fields

| Field | Type | Pre-filled from |
|---|---|---|
| Commute mode | Dropdown (all 9 modes) | Gemini guess or current profile |
| Distance (km) | Number, min=0, max=500 | Gemini guess or today's log |
| AC hours | Number, min=0, max=24 | Current profile default |
| Diet type | Dropdown (4 options) | Current profile default |

---

## 4. Scroll Layout & Navigation

### Layout Rules

| Section | Type | Notes |
|---|---|---|
| Landing | Full page | Login/signup — no scroll needed |
| Onboarding | Full page | Form needs focused attention |
| Dashboard | Single scroll | Score → Suggestions → Chat → Simulator → Streak |
| Quiz | Full page | Needs full attention |
| Leaderboard | Full page | Separate context |
| Profile | Full page | Settings + badges |

### Dashboard Scroll Order

```
1. ScoreBreakdown (pie chart)
2. SuggestionsList
3. ChatSection (embedded)
4. SimulatorSection (embedded — sliders + live pie)
5. StreakCounter + LeaderboardSnippet
```

### Navigation

- Top-right anchor nav on scroll pages: links to each section
- Bottom navigation bar on mobile — not hamburger
- Anchor links use smooth scroll with `prefers-reduced-motion` check

---

## 5. Mobile-First Rules

| Rule | Specification |
|---|---|
| Minimum width | 360px |
| Max content width | 480px mobile, 768px tablet, 1024px desktop |
| Touch targets | Min 44×44px on all interactive elements |
| Font size minimum | 16px base body text |
| Line height | 1.5 minimum |
| Form inputs | Full width on mobile — never side-by-side < 480px |
| Sliders | Min 24px track height for thumb dragging |
| Chat input | Sticky to bottom — keyboard does not push it off screen |
| Score number | Min 32px — visible at a glance |
| Pie chart | Min 200×200px on mobile — slices labelled outside on desktop, tooltip on mobile |

### Loading & Network States — Required on Every API Call

| State | What to Show |
|---|---|
| Loading | Skeleton or spinner — never blank |
| Success | Data rendered |
| Error | Inline message + retry option |
| Offline | "Check your connection and try again" |

### Tap Rules

- ✅ 44×44px touch area via padding (visual size can be smaller)
- ✅ Submit buttons full-width on mobile
- ✅ Dropdowns use native `<select>` on mobile
- ❌ No hover-only interactions

---

## 6. Language — Plain English Rules

### Writing Rules

| Rule | ❌ Bad | ✅ Good |
|---|---|---|
| No technical terms | "Parse failed" | "Couldn't understand that — try the form below" |
| No jargon | "Baseline CO2 delta" | "How much more or less than usual" |
| No passive voice | "Your data is being processed" | "Saving your update..." |
| No error codes | "Error 422" | "Something looks off — check the form" |
| Specific over vague | "Invalid input" | "Enter a distance between 0 and 500 km" |
| Positive framing | "You failed to log today" | "Log today to keep your streak alive 🔥" |
| Action-first CTAs | "Submit" | "Save my habits" / "See my score" |

### Tone by Context

| Context | Tone | Example |
|---|---|---|
| Onboarding | Welcoming, low-pressure | "Takes 2 minutes — let's get your baseline" |
| Dashboard greeting | Personal, warm | "Good morning, Priya 🌿" |
| Positive delta | Celebratory | "You saved 1.6 kg today — like charging 194 fewer phones 🔋" |
| Negative delta | Non-judgmental | "A bit higher today — that's okay. Small changes add up." |
| Streak broken | Encouraging | "Streak reset — your progress isn't. Start again today 🔥" |
| Suggestion | Specific, actionable | "Try metro tomorrow instead of your two-wheeler — saves ~0.8 kg CO2" |
| Error | Calm | "Something went wrong. Please try again in a moment." |
| Bot follow-up | Natural, one question | "How many km was the trip?" — never a list of questions |

---

## 7. Form Validation Messages

All validation errors are inline (below the field), specific, plain English. No modal popups for field errors.

| Field | ❌ Bad | ✅ Required |
|---|---|---|
| `avg_daily_km` over 500 | "Value out of range" | "Enter a distance between 0 and 500 km" |
| `avg_daily_km` negative | "Invalid value" | "Distance can't be negative" |
| `ac_hours_per_day` over 24 | "Invalid hours" | "AC hours can't be more than 24 in a day" |
| `commute_mode` not selected | "Required field" | "Please select your main way of getting around" |
| `diet_type` not selected | "Required field" | "Please select the option that best describes how you eat" |
| `message` empty | "Field required" | "Type what changed in your habits today" |
| `message` HTML detected | "Invalid characters" | "Plain text only — no special formatting needed" |
| `name` empty | "Required" | "What should we call you?" |
| Network error | "Error" | "Couldn't save right now — check your connection and try again" |

### Validation Timing

| Trigger | Behaviour |
|---|---|
| On submit | Validate all fields — show all errors at once |
| On blur | Validate that single field inline |
| On typing | Only for character count (chat 500 limit) |
| On load | Never show errors on a fresh form |

---

## 8. Semantic HTML & ARIA

### Required Structure

| Element | Usage |
|---|---|
| `<main>` | One per page |
| `<header>` | App header |
| `<nav>` | Bottom navigation |
| `<section>` | Each scroll section (score, chat, simulator) |
| `<h1>` | One per page |
| `<h2>` | Section headings |
| `<label>` | Every form input — `for` attribute |
| `<fieldset>` + `<legend>` | Groups of related inputs |
| `<button>` | All clickable actions — never `<div onClick>` |

### ARIA Live Regions

| Region | Type | Announces |
|---|---|---|
| Score update after confirm | `aria-live="polite"` | New CO2 total + analogy |
| Bot reply in chat | `aria-live="polite"` | Bot message text |
| Form validation errors | `aria-live="assertive"` | Error immediately |
| Loading states | `aria-busy="true"` | Screen reader waits |
| Streak update | `aria-live="polite"` | New streak count |

### ARIA Label Reference

| Element | Required `aria-label` |
|---|---|
| Pie chart (ScoreBreakdown) | `"Today's carbon breakdown: Transport 1.7kg, Diet 5.0kg, Electricity 1.5kg, LPG 0kg"` |
| Simulator pie chart | Updated dynamically as sliders move |
| CO2 total number | `"Today's carbon score: 3.5 kg CO2"` |
| Streak counter | `"Current logging streak: 5 days"` |
| Confirm button | `"Confirm: Switch to Metro, 8 km"` |
| Edit button | `"Edit this update"` |
| Fire emoji | `aria-hidden="true"` |
| Badge icons | `aria-label="[Badge name] badge"` |
| Simulator slider | `aria-label="Daily commute distance, currently 10 km"` |
| Dismiss suggestion | `aria-label="Dismiss: Try metro tomorrow"` |

---

## 9. Keyboard Navigation

| Interaction | Keyboard |
|---|---|
| Tab through form | Top-to-bottom visual order |
| Submit form | `Enter` or Tab to button + `Enter` |
| Chat submit | `Enter` in message input |
| Simulator sliders | Arrow keys |
| Quiz answers | `Tab` to option, `Space` to select |
| Confirm ParsePreview | `Tab` to Confirm, `Enter` |
| Skip to main content | First `Tab` reveals skip link |
| Close any overlay | `Escape` |

---

## 10. Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  /* Applied globally — no component opts out */
  all transitions → disabled
  all animations → disabled
  pie chart entrance animation → instant render
  streak fire pulse → static icon
  scroll animations → disabled
  chart draw animations → instant
}
```

---

## 11. Colour & Contrast

| Element | Foreground | Background | Ratio | Pass |
|---|---|---|---|---|
| Body text | `#1f2937` | `#ffffff` | 16:1 | ✅ AAA |
| Secondary text | `#6b7280` | `#ffffff` | 4.6:1 | ✅ AA |
| CO2 score | `#111827` | `#f9fafb` | 19:1 | ✅ AAA |
| Positive delta | `#166534` | `#dcfce7` | 7.2:1 | ✅ AAA |
| Negative delta | `#991b1b` | `#fee2e2` | 6.8:1 | ✅ AAA |
| Button text | `#ffffff` | `#16a34a` | 4.7:1 | ✅ AA |
| Error text | `#991b1b` | `#ffffff` | 8.6:1 | ✅ AAA |
| Pie — Transport | `#3b82f6` (blue-500) | white bg | 3.1:1 | Label required |
| Pie — Diet | `#22c55e` (green-500) | white bg | 3.1:1 | Label required |
| Pie — Electricity | `#f59e0b` (amber-500) | white bg | 2.7:1 | Label required |
| Pie — LPG | `#ef4444` (red-500) | white bg | 3.9:1 | Label required |

> **Pie chart slices:** contrast ratios are below AA for text on coloured background — all slices must include text labels and/or tooltips. Colour alone is never the only indicator.

---

## 12. Pre-Build Checklist

**India / Mobile**
- [ ] Layout works at 360px
- [ ] All tap targets ≥ 44×44px
- [ ] All API calls have loading, success, and error states
- [ ] No hover-only interactions
- [ ] Units are km and kg throughout
- [ ] Chat input accepts Unicode and emoji

**Persona**
- [ ] Dynamic text adapts to user's persona
- [ ] Suggestions exclude irrelevant habits for that persona
- [ ] Commute dropdown prominence matches persona

**Fallback & Chat**
- [ ] Chat always shows form option
- [ ] Low-confidence parse shows QuickUpdateForm with pre-fills
- [ ] Bot language is natural — no technical phrases
- [ ] Max 3 chat turns then auto-show form
- [ ] Emoji shorthand pre-processed before Gemini

**Score & Simulator**
- [ ] Score shown as pie chart with breakdown — not just a number
- [ ] Simulator has no Apply button
- [ ] Simulator pie updates live on slider move (debounced 200ms)
- [ ] "Log these changes" pre-fills chat

**Semantic & ARIA**
- [ ] One `<h1>` per page
- [ ] All inputs have `<label>`
- [ ] Error containers have `role="alert"`
- [ ] Loading states set `aria-busy="true"`
- [ ] Pie charts have `aria-label` with all values
- [ ] Icon-only elements have `aria-label` or `aria-hidden`

**Colour & Motion**
- [ ] Status conveyed by text + colour — never colour alone
- [ ] Pie chart slices all have text labels
- [ ] All text meets WCAG AA contrast
- [ ] `prefers-reduced-motion` applied globally

---

*ACCESSIBILITY.md Version 1.0 — Zerofy India*