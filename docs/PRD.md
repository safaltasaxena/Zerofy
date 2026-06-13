# Zerofy India — Product Requirements Document (PRD)

> **Hackathon:** Google Promptwars Virtual Hackathon — Challenge 3  
> **Version:** 1.0  
> **Stack:** Python (FastAPI) + React + Firestore + Gemini API  
> **Target Region:** India  

---

## 1. Product Overview

### 1.1 What is Zerofy India?

Zerofy India is an AI-powered carbon footprint awareness platform designed for Indian users across all life stages. Unlike generic carbon calculators, Zerofy acts as a **real-time conversational sustainability coach** — it understands your lifestyle, tracks changes through natural conversation, simulates your potential impact, and keeps you engaged through awareness-based gamification.

### 1.2 Problem Being Solved

Most people have no idea how their daily habits contribute to carbon emissions. Existing tools are either too complex, too generic, or culturally irrelevant for Indian users. Zerofy bridges this gap with:

- Culturally relevant suggestions (autos, metro, LPG, Indian diet)
- Conversational habit tracking — no tedious forms every day
- Relatable impact storytelling — not just raw CO2 numbers
- Engagement through learning through quizzes and gamification of habits and streaks displayed through  leaderboard.

### 1.3 Target Users (Verticals)

| Persona | Description |
|---|---|
| 🎒 Student | Hostel/college life, campus commute, canteen food |
| 💼 Working Professional | Office commute, WFH energy, lunch habits |
| 👨‍👩‍👧 Family / Parent | Household appliances, car pooling, cooking gas |
| 👦 Teenager | School commute, screen time energy, food choices |
| 🧓 Senior Citizen | Home cooling, cooking habits, local travel |

---

## 2. Core Principles

- **No fake data** — gamification rewards verified engagement, not self-reported CO2 claims
- **India-first** — emission factors, suggestions, and analogies are specific to India
- **Persona-aware** — every suggestion, quiz, and challenge adapts to the user's life stage
- **Depth over breadth** — fewer features, done really well
- **Fallback always exists** — if AI parsing fails, graceful degradation to quick-update form

---

## 3. Feature Specifications

---

### Feature 1 — User Onboarding & Profile Setup

**Type:** Core  
**Complexity:** Low  
**Who sees it:** First-time users only

#### Description
A one-time smart form that captures the user's baseline lifestyle habits to generate their initial carbon footprint score.

#### Form Fields

| Field | Type | Options/Notes |
|---|---|---|
| Name | Text | — |
| State / City | Dropdown | Indian states + major cities |
| Persona | Dropdown | Student / Working Professional / Family / Teenager / Senior |
| Primary commute mode | Dropdown | Walk, Bicycle, Two-wheeler (petrol), Two-wheeler (electric), Auto, Bus/BEST, Metro, Car (petrol), Car (diesel), Car (electric), WFH |
| Average daily commute distance | Number | In km |
| Diet type | Dropdown | Vegetarian, Eggetarian, Non-vegetarian, Vegan |
| Monthly electricity units | Number | Approximate units/month |
| AC usage | Number | Hours per day (0 if no AC) |
| LPG cylinder usage | Number | Cylinders per month (approximate) |

#### Output
- Baseline daily CO2 score (kg)
- Baseline monthly CO2 score (kg)
- First 3 personalised suggestions based on persona
- Analogy equivalent shown alongside score

#### Rules
- Form appears only once — on first login
- User can choose to re-fill form anytime from settings
- All fields except name are required
- Form validates input ranges (e.g. commute distance cannot be 9999 km)

---

### Feature 2 — NLP Chat — Habit Updates

**Type:** Core  
**Complexity:** Medium  
**Who sees it:** Returning users, every day

#### Description
Returning users update their habits through natural conversation instead of filling forms. The bot parses their message, extracts structured data using Gemini, updates the database, and gives instant feedback.

#### User Flow

```
User types → Gemini parses → Preview shown → User confirms → DB updated → Feedback given
```

#### Conversation Examples

| User says | Bot understands | Bot asks follow-up |
|---|---|---|
| "took metro today" | transport change | "How many km was the trip?" |
| "skipped AC today" | AC usage = 0 | None needed |
| "walked 3km to college instead of auto" | walking 3km, no auto | None needed |
| "used car today" | transport change to car | "How many km did you drive?" |

#### Guided Follow-up Logic
- If user gives partial info → bot asks ONE follow-up question
- If user gives complete info → confirm and update immediately
- Bot never asks more than 2 questions per update
- After update: show CO2 impact + analogy + encouragement message

#### Fallback
- If Gemini parsing confidence is low → show quick-update form with pre-filled guesses
- User can always choose "update via form" from chat
- All parsing errors are logged silently — user never sees a crash

#### Real-time Preview (UI)
Before confirming, user sees a badge:
```
[Action: Transport → Metro | Distance: 8km] [Confirm ✅] [Edit ✏️]
```

---

### Feature 3 — Carbon Calculator Engine

**Type:** Core (internal utility)  
**Complexity:** Low  
**Who sees it:** Never directly — powers everything

#### Description
The core calculation brain of the app. Never shown directly but called by every feature that deals with CO2 numbers.

#### India-Specific Emission Factors

| Category | Factor | Source basis |
|---|---|---|
| Indian electricity grid | ~0.82 kg CO2 per kWh | CEA India average |
| Petrol two-wheeler | ~0.05 kg CO2 per km | |
| Petrol car | ~0.17 kg CO2 per km | |
| Diesel car | ~0.15 kg CO2 per km | |
| Auto rickshaw | ~0.07 kg CO2 per km | |
| Bus / BEST | ~0.02 kg CO2 per km per passenger | |
| Metro | ~0.01 kg CO2 per km per passenger | |
| Walking / Cycling | 0 kg CO2 | |
| Electric vehicle | ~0.02 kg CO2 per km (Indian grid) | |
| Non-vegetarian diet | ~5.0 kg CO2 per day | |
| Vegetarian diet | ~2.5 kg CO2 per day | |
| Vegan diet | ~1.5 kg CO2 per day | |
| LPG cylinder | ~12 kg CO2 per cylinder | |

#### Functions Exposed
- `calculate_daily_score(user_profile)` → daily kg CO2
- `calculate_monthly_score(user_profile)` → monthly kg CO2
- `calculate_delta(old_habits, new_habits)` → kg saved or added
- `simulate_changes(user_profile, simulated_changes)` → hypothetical score

---

### Feature 4 — Personalised Suggestions Engine

**Type:** Core  
**Complexity:** Medium  
**Who sees it:** Dashboard, after chat updates, after onboarding

#### Description
Generates 3 personalised, actionable suggestions based on the user's current habits and persona. Does NOT suggest things the user already does well.

#### Logic Flow

```
1. Rule-based layer checks user's current habits
2. Identifies top 3 improvement areas
3. Filters out already-good habits
4. Selects suggestion templates for user's persona
5. Passes through Gemini to make language warm and human
6. Returns 3 specific, actionable suggestions
```

#### Persona-Specific Suggestion Examples

**Student:**
- "Switch off your hostel fan during class hours — saves ~0.3 kg CO2/day"
- "Walk to the library instead of taking the shuttle 3 times a week"
- "Choose dal-rice at the canteen over chicken twice a week"

**Working Professional:**
- "Carpool with a colleague 2 days a week — cuts your commute emissions by 40%"
- "Turn off your workstation monitor when stepping away for lunch"
- "Work from home one extra day — saves your entire commute footprint that day"

**Family:**
- "Run the washing machine with full loads only — saves ~1.2 units/week"
- "Reduce AC temperature by 1°C — cuts electricity usage by ~6%"
- "Try one vegetarian dinner per week as a family"

#### Rules
- Max 3 suggestions shown at once
- Suggestions refresh after each habit update
- Never repeat a suggestion already completed or marked as irrelevant
- User can dismiss a suggestion and get a replacement

---

### Feature 5 — Relatable Analogies Engine

**Type:** Core (utility)  
**Complexity:** Low  
**Who sees it:** Everywhere a CO2 number appears

#### Description
A standalone utility module that converts raw CO2 kg values into things people actually understand. Never shows a raw number alone.

#### Analogy Mapping

| CO2 (kg) | Analogy |
|---|---|
| 1 kg CO2 | Charging ~121 smartphones |
| 1 kg CO2 | Running a ceiling fan for ~20 hours |
| 1 kg CO2 | Running an LED bulb for ~90 hours |
| 1 kg CO2 | ~15 days for a mature tree to absorb |
| 1 kg CO2 | Driving a petrol bike for ~20 km |
| 1 kg CO2 | Cooking ~4 meals on LPG |

#### Display Logic
- Pick the most contextually relevant analogy based on what the user just did
  - Transport update → show bike/car analogy
  - Electricity update → show fan/bulb analogy
  - Diet update → show cooking/meals analogy
- Always show analogy in the format: `"That's like charging 218 phones 🔋"`

---

### Feature 6 — What-If Simulator

**Type:** Core (WOW feature)  
**Complexity:** Low  
**Who sees it:** Dedicated simulator page

#### Description
An interactive simulator with sliders that shows users how much they could save if they changed specific habits. Pure math — no AI calls — so it's instant.

#### Simulator Categories & Sliders

| Category | Slider | Unit |
|---|---|---|
| Transport | Reduce car/two-wheeler usage | % reduction |
| Transport | Increase walking/cycling | km per day |
| Diet | Switch meals to vegetarian | meals per week |
| Electricity | Reduce AC usage | hours per day |
| Electricity | Reduce general electricity | % reduction |
| LPG | Reduce cylinder usage | cylinders per month |

#### Output (updates in real-time as sliders move)

```
Potential weekly saving: 4.2 kg CO2
That's like not charging 508 phones 🔋
Projected monthly saving: 18.3 kg CO2
Equivalent to planting 1.2 trees 🌳
```

#### Rules
- No API calls — pure frontend math using emission constants
- Sliders start at user's current values
- Output updates on every slider change (debounced 200ms)
- "Apply these changes" button → pre-fills chat with suggested update

---

### Feature 7 — Gamification System

**Type:** Bonus  
**Complexity:** Low-Medium  
**Who sees it:** Dashboard, profile page

#### Philosophy
> Rewards verified engagement and learning — NOT self-reported CO2 outcomes (which are fakeable).

#### Awareness Score
Points are earned by:

| Action | Points |
|---|---|
| Daily login + habit log | +10 |
| Completing daily quiz | +15 |
| Correct quiz answer | +5 per question |
| Using the simulator | +5 |
| 7-day streak | +50 bonus |
| Completing full onboarding | +20 |
| Exploring all simulator categories | +10 |

**NOT based on CO2 numbers** — this prevents gaming the system.

#### Streaks
- Daily login + log streak 🔥
- Daily quiz completion streak
- Streak resets at midnight if not logged

#### Badges

| Badge | Trigger |
|---|---|
| 🌱 First Step | Logged habits for the first time |
| 🔥 Week Warrior | 7-day logging streak |
| 🧠 Quiz Starter | Completed first quiz |
| 🎓 Quiz Master | Answered 20 questions correctly |
| 🔍 Simulator Explorer | Tried all simulator categories |
| 📋 Profile Pro | Completed full onboarding form |
| 🌍 Month Warrior | Active for 30 consecutive days |
| ⚡ Early Adopter | Joined in first week of launch |

#### Leaderboard
- Ranked by **Awareness Score only** — not CO2 numbers
- Filtered by **state** — Mumbai users compete with Mumbai users
- Weekly reset — gives new users a chance every week
- Shows: Rank, Name (first name only), Awareness Score, Top badge

---

### Feature 8 — Daily Awareness Quiz

**Type:** Bonus  
**Complexity:** Low  
**Who sees it:** Dashboard (quiz card), dedicated quiz page

#### Description
3 MCQ questions per day, tied to the user's persona and habits. Completing the quiz earns streak points. Wrong answers show a brief educational explanation.

#### Question Design Rules
- Questions are contextual — tied to user's actual habits when possible
- 4 options per question
- One correct answer
- Wrong answer shows: why it's wrong + correct fact (1-2 sentences)
- Questions rotate — no repeats within 30 days

#### Example Questions by Persona

**Student:**
- "Which uses more electricity — ceiling fan for 8 hours or laptop charger for 3 hours?"
- "How much CO2 does one petrol auto trip of 5km produce approximately?"

**Working Professional:**
- "Carpooling with one colleague reduces your commute emissions by approximately what %?"
- "Which generates more CO2 — AC at 18°C for 4 hours or at 24°C for 4 hours?"

**Family:**
- "Which cooking method uses the least LPG per meal?"
- "A fully loaded washing machine vs half-loaded — what's the energy difference?"

#### Question Bank
- Minimum 90 questions at launch (30 per major persona group)
- Questions tagged by persona, category, and difficulty

---

## 4. System Architecture

### 4.1 High-Level Overview

```
┌─────────────────────────────────────────┐
│              React Frontend             │
│  Onboarding │ Chat │ Dashboard │ Sim    │
└─────────────────┬───────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────┐
│           FastAPI Backend               │
│                                         │
│  ┌──────────┐  ┌──────────┐            │
│  │ Carbon   │  │Suggestion│            │
│  │Calculator│  │ Engine   │            │
│  └──────────┘  └──────────┘            │
│                                         │
│  ┌──────────┐  ┌──────────┐            │
│  │ Analogy  │  │ Gemini   │            │
│  │ Engine   │  │ Parser   │            │
│  └──────────┘  └──────────┘            │
│                                         │
│  ┌──────────┐  ┌──────────┐            │
│  │Simulator │  │Gamifi-   │            │
│  │ Engine   │  │cation    │            │
│  └──────────┘  └──────────┘            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              Firestore DB               │
│  users │ profiles │ logs │ gamification │
└─────────────────────────────────────────┘
```

### 4.2 Folder Structure

```
Zerofy-india/
│
├── backend/
│   ├── config/
│   │   └── firebase.py              # Firestore connection
│   ├── constants/
│   │   └── emission_factors.py      # All CO2 multipliers (India-specific)
│   ├── utils/
│   │   ├── analogy_engine.py        # CO2 → human-scale analogies
│   │   ├── gemini_parser.py         # NLP parsing via Gemini API
│   │   └── suggestion_engine.py     # Rule-based + Gemini suggestions
│   ├── routes/
│   │   ├── user.py                  # Onboarding & profile endpoints
│   │   ├── logs.py                  # Chat updates & daily logs
│   │   ├── simulator.py             # What-if calculations
│   │   ├── quiz.py                  # Daily quiz endpoints
│   │   └── gamification.py          # Streaks, badges, leaderboard
│   ├── tests/
│   │   ├── test_calculator.py       # Unit tests for CO2 math
│   │   ├── test_analogies.py        # Unit tests for analogy engine
│   │   └── test_suggestions.py      # Unit tests for suggestion logic
│   ├── main.py                      # FastAPI app entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── OnboardingForm.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Simulator.jsx
│   │   │   ├── Leaderboard.jsx
│   │   │   ├── DailyQuiz.jsx
│   │   │   └── BadgeShelf.jsx
│   │   ├── utils/
│   │   │   └── api.js               # All API call functions
│   │   └── App.jsx
│   └── package.json
│
├── .gitignore                        # Excludes node_modules, .env, __pycache__
├── README.md                         # Hackathon pitch document
└── PRD.md                            # This file
```

---

## 5. API Endpoints

### Users & Profile

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/user/register` | Create new user account |
| POST | `/api/user/profile` | Submit onboarding form, get baseline score |
| GET | `/api/user/profile/{user_id}` | Get user profile + current score |
| PUT | `/api/user/profile/{user_id}` | Re-submit full form (optional) |

### Logs & Chat Updates

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/logs/chat-update` | NLP chat input → parse → update |
| GET | `/api/logs/{user_id}/today` | Get today's log |
| GET | `/api/logs/{user_id}/weekly` | Get weekly trend data |

### Simulator

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/simulator/calculate` | Run what-if calculation |

### Quiz

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/quiz/today/{user_id}` | Get today's 3 questions |
| POST | `/api/quiz/submit` | Submit answers, get results + points |

### Gamification

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/gamification/{user_id}` | Get streaks, badges, awareness score |
| GET | `/api/leaderboard/{state}` | Get weekly leaderboard for a state |

---

## 6. Database Schema (Firestore)

### Collection: `users`
```json
{
  "user_id": "string",
  "name": "string",
  "email": "string",
  "state": "string",
  "city": "string",
  "persona": "student | professional | family | teenager | senior",
  "created_at": "timestamp",
  "is_onboarded": "boolean"
}
```

### Collection: `profiles`
```json
{
  "user_id": "string",
  "commute_mode": "string",
  "avg_daily_km": "number",
  "diet_type": "string",
  "monthly_electricity_units": "number",
  "ac_hours_per_day": "number",
  "lpg_cylinders_per_month": "number",
  "baseline_daily_co2_kg": "number",
  "baseline_monthly_co2_kg": "number",
  "last_updated": "timestamp"
}
```

### Collection: `daily_logs`
```json
{
  "log_id": "string",
  "user_id": "string",
  "date": "string",
  "commute_mode": "string",
  "commute_km": "number",
  "ac_hours": "number",
  "diet_type": "string",
  "daily_co2_kg": "number",
  "delta_from_baseline_kg": "number",
  "source": "chat | form"
}
```

### Collection: `gamification`
```json
{
  "user_id": "string",
  "awareness_score": "number",
  "log_streak": "number",
  "quiz_streak": "number",
  "last_log_date": "string",
  "last_quiz_date": "string",
  "badges": ["array of badge IDs"],
  "weekly_score": "number",
  "week_start": "timestamp"
}
```

### Collection: `quiz_results`
```json
{
  "user_id": "string",
  "date": "string",
  "questions": ["array of question IDs"],
  "answers": ["array of selected options"],
  "correct_count": "number",
  "points_earned": "number"
}
```

---

## 7. Scoring Criteria Mapping

| Judging Parameter | How We Address It |
|---|---|
| **Code Quality** | Separated utilities (analogy engine, suggestion engine, gemini parser as independent modules), clean folder structure, consistent naming |
| **Security** | No API keys in code (env variables), input validation on all endpoints, Firestore security rules, no sensitive data in logs |
| **Efficiency** | Simulator uses pure math (no LLM), Gemini only called when necessary, Firestore queries use indexed fields |
| **Testing** | Dedicated `/tests` folder with unit tests for calculator and analogy engine, FastAPI auto-generates interactive docs |
| **Accessibility** | Persona dropdown ensures relevant UX for all ages, graceful fallback when NLP fails, simple clean UI, India-specific language and references |
| **Problem Statement Alignment** | Covers understand (analogies + quiz), track (daily logs + dashboard), reduce (suggestions + simulator) — all three verbs of the problem statement |

---

## 8. Consciously Out of Scope

| Feature | Reason |
|---|---|
| Google Maps live distance | Hard dependency, risky, can be replaced by manual km input |
| Steps tracker API (Google Fit) | Platform-specific, complex, out of scope for hackathon |
| Real-world rewards | Cannot be backed up honestly |
| CO2-based leaderboard | Fakeable — replaced with Awareness Score |
| Social sharing | Nice to have, not core |
| Push notifications | Out of scope for web version |

---

## 9. Implementation Timeline

| Day | Focus |
|---|---|
| Day 1 | Repo setup, Firestore config, folder structure, .gitignore |
| Day 2 | Emission constants, Carbon calculator, Analogy engine |
| Day 3 | Onboarding form (frontend + backend), baseline score generation |
| Day 4 | Gemini NLP parser, chat interface, guided follow-up logic |
| Day 5 | Suggestions engine, what-if simulator |
| Day 6 | Gamification system, daily quiz |
| Day 7 | Dashboard UI, polish, analogy integration everywhere |
| Day 8+ | Testing, README, bug fixes, final submission |

---

## 10. README Pitch (Key Lines)

> *"Zerofy India is a real-time conversational sustainability coach for Indian users. Unlike static carbon calculators, it adapts to your persona, understands natural language habit updates, and makes your impact tangible through culturally relevant analogies. To prevent data manipulation, our engagement system rewards verified behaviour like quiz participation and daily logging — not self-reported outcomes."*

---

*PRD Version 1.0 — Zerofy India*
