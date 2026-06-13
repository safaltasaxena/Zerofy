# Zerofy India — Efficiency Specification
**Stack:** Python (FastAPI) + React + Firestore + Gemini API | **Version:** 1.1
**Deployment:** Backend → GCP Cloud Run | Frontend → Vercel

---

## Core Principles

> **Gemini is expensive and slow. Call it only when math cannot do the job.**
> **The Simulator must never touch an LLM. It is pure math, always instant.**
> **Single source of truth for constants — `/api/constants` endpoint, no dual files.**
> **Every Firestore query must be predictable in cost — no open-ended scans.**
> **The frontend never waits for data it already has.**

---

## 1. Constants — Single Source of Truth

The old approach (Python file + JS file manually synced) is replaced entirely.

### New Flow

```
backend/constants/emission_factors.py  ← only place numbers live
        ↓
GET /api/constants                     ← public endpoint, no auth
        ↓
Frontend fetches once on app start
        ↓
Stored in module-level JS variable (constants.js)
        ↓
Simulator uses this variable — synchronous, instant
```

### Rules

- ✅ `emission_factors.py` is the single source of truth — edit only here
- ✅ Frontend always reads from the module-level variable populated by `/api/constants`
- ✅ `/api/constants` is cached at CDN level — no backend load
- ✅ Simulator `simulate()` function uses this variable synchronously — no fetch during slider movement
- ❌ No hardcoded emission numbers anywhere in frontend code
- ❌ No `emissionFactors.js` file with hardcoded values — this pattern is eliminated

---

## 2. When to Call Gemini — and When NOT To

### Decision Matrix

| Situation | Call Gemini? | Reason | What to Use Instead |
|---|---|---|---|
| User sends natural language chat message | ✅ Yes | Only task requiring NLP | `gemini_parser.py` |
| Suggestion language polish | ✅ Yes | Rules produce stiff output | `suggestion_engine.py` → Gemini pass |
| Daily quiz generation | ✅ Yes — once per day | Static JSON can't personalise to worst habit | `quiz.py` → cached in Firestore |
| Carbon score calculation | ❌ No | Pure math | `utils/calculator.py` |
| Monthly score calculation | ❌ No | Pure math | `utils/calculator.py` |
| Score breakdown (pie chart) | ❌ No | Pure math per category | `calculate_breakdown()` |
| Delta calculation | ❌ No | Pure subtraction | `utils/calculator.py` |
| Simulator what-if | ❌ No | Pure math — must be instant | Frontend `simulate()` |
| Analogy generation | ❌ No | Lookup table | `utils/analogy_engine.py` |
| Leaderboard query | ❌ No | Pure DB query | Firestore index |
| Serving cached quiz | ❌ No | Already generated today | Firestore read |
| Streak / badge calculation | ❌ No | Pure date logic | `gamification` route |
| Onboarding baseline score | ❌ No | Pure math | `calculate_daily_score()` |

### Gemini Call Budget Per User Action

| User Action | Max Gemini Calls | Notes |
|---|---|---|
| Chat message submitted | 1 (+ 1 retry) | Hard cap |
| Dashboard load | 0 | All Firestore + math |
| Suggestion refresh after chat | 1 | Polish pass only — rules run first |
| Onboarding submitted | 0 | Pure math |
| Simulator slider moved | 0 | Pure frontend math |
| Quiz page — first load today | 1 | Generated + cached in Firestore |
| Quiz page — subsequent loads | 0 | Served from Firestore |
| Leaderboard viewed | 0 | Pure DB query |
| Profile page loaded | 0 | Pure DB read |

---

## 3. Simulator — Pure Math, No Apply Button

The Simulator is embedded in the dashboard scroll. Sliders update a pie chart in real time.

### Architecture Rule

```
Slider moves
      ↓
Frontend simulate() runs locally
      ↓
Uses constants loaded from /api/constants (already in memory)
      ↓
SimulatorBreakdown pie chart updates (debounced 200ms)
      ↓
No API call. No Firestore read. No Gemini.
      ↓
User clicks "Log these changes"
      ↓
Pre-fills chat input — chat handles the actual DB update
```

### Simulator Rules

| Rule | Detail |
|---|---|
| All math runs in the browser | `simulate()` is pure and synchronous — no async, no await |
| Constants from memory | Loaded once from `/api/constants` on app start — not re-fetched per slider move |
| No Apply button | Removed — "Log these changes" feeds into chat |
| Pie chart updates live | `SimulatorBreakdown` re-renders on every debounced slider event |
| Backend `/api/simulator/calculate` | Exists for validation only — never called during live slider use |

### What the Simulator Never Does

- ❌ Never calls Gemini
- ❌ Never writes to Firestore during slider movement
- ❌ Never calls the backend during slider movement
- ❌ Never re-fetches constants on slider change
- ❌ Never has an Apply button

---

## 4. Debounce Rules

| Interaction | Delay | Why |
|---|---|---|
| Simulator slider move | 200ms | Prevents 60 re-renders/second on drag |
| Chat message typing (char count) | 100ms | UI feedback only — no API call |
| Search / filter inputs | 300ms | Avoids premature queries |
| Form field validation | On blur only | No debounce — validate when field loses focus |

### Rules

- ✅ Single shared debounce utility — never re-implemented per component
- ✅ Debounce wraps the calculation function — not the state setter
- ✅ Cancel pending debounce on component unmount (useEffect cleanup)
- ❌ Never debounce Confirm or Submit — deliberate user actions
- ❌ Never debounce error clearing — errors disappear immediately when corrected

---

## 5. Firestore Query Rules

### Query Pattern Reference

| Query | Collection | Filter / Order | Index Required | Frequency |
|---|---|---|---|---|
| Get user profile | `profiles/{user_id}` | Document ID lookup | ❌ | Every page load |
| Get today's log | `daily_logs/{user_id}_{date}` | Document ID lookup | ❌ | Dashboard, chat update |
| Get weekly trend | `daily_logs` | `user_id == x` + `date >= 7 days ago` order `date` | ✅ `user_id + date` | Dashboard — `GET /api/logs/{user_id}/weekly` |
| Get gamification | `gamification/{user_id}` | Document ID lookup | ❌ | Dashboard, profile |
| Get state leaderboard | `gamification` | `state == x` order `weekly_score DESC` | ✅ `state + weekly_score` | Leaderboard page |
| Get today's quiz | `quiz_results/{user_id}_{date}` | Document ID lookup | ❌ | Quiz page |

### Firestore Indexes (`firestore.indexes.json`)

| Index | Collection | Fields | Order |
|---|---|---|---|
| Weekly trend | `daily_logs` | `user_id` ASC, `date` ASC | Ascending |
| State leaderboard | `gamification` | `state` ASC, `weekly_score` DESC | Mixed |

### Query Rules

- ✅ Document ID lookups preferred — O(1), no index
- ✅ `.limit(7)` on weekly trend, `.limit(50)` on leaderboard
- ❌ Never query `daily_logs` without `user_id` filter
- ❌ Never `orderBy` on unindexed field
- ❌ Never fetch full collection to filter in memory

### Write Rules

| Operation | Rule |
|---|---|
| Daily log | Upsert by `{user_id}_{date}` — never duplicate |
| Quiz result | Upsert by `{user_id}_{date}` — one per user per day |
| Gamification | Backend Admin SDK only — client never writes directly |
| Streak | Read → compute → write in single backend function |
| Leaderboard score | Updated only when gamification doc changes |

---

## 6. Caching — What to Cache vs Fetch Fresh

### Cache Decision Matrix

| Data | Cache? | Where | Invalidation |
|---|---|---|---|
| Emission constants | ✅ Yes | Module-level JS variable | Never — fetched once on app start |
| User profile | ✅ Yes | React state | On form re-submit |
| Today's CO2 score + breakdown | ✅ Yes | React state | On chat confirm |
| Analogy strings | ✅ Yes | In-memory (analogy_engine) | Never — pure constants |
| Quiz questions (today) | ✅ Yes | React state + Firestore | Midnight (new day) |
| Leaderboard | ✅ Yes | React state | On page revisit |
| Weekly trend chart | ✅ Yes | React state | After chat confirm |
| Gamification (streaks, badges) | ✅ Yes | React state | After any point-earning action |
| Firebase auth token | ✅ Yes | Memory only | Firebase auto-refreshes at 1hr |
| Today's log | ✅ Yes | React state | On chat confirm |
| Gemini parse response | ❌ No | Never cached | Non-deterministic |
| Past 90 days of logs | ❌ No | Never bulk-fetched | Fetch only 7 needed |

### State Invalidation Triggers

| User Action | State Invalidated |
|---|---|
| Chat update confirmed | Score, breakdown, today's log, gamification, suggestions |
| Quiz submitted | Gamification (streak, points), quiz result |
| Onboarding submitted | Profile, score, breakdown, suggestions |
| Profile re-fill submitted | Profile, score, breakdown, suggestions |
| Simulator "Log these changes" | Nothing — feeds into chat, chat handles invalidation |

---

## 7. API Call Budget Per Page

| Page | Allowed Calls | Calls Made |
|---|---|---|
| App start (any page) | 1 | `GET /api/constants` — once, module-level |
| `/dashboard` | 3 | `GET /api/user/profile`, `GET /api/logs/{user_id}/today`, `GET /api/gamification/{user_id}` |
| `/quiz` | 1 | `GET /api/quiz/today/{user_id}` |
| `/leaderboard` | 1 | `GET /api/leaderboard/{state}` |
| `/profile` | 2 | `GET /api/user/profile`, `GET /api/gamification/{user_id}` |
| `/onboarding` | 0 | Form only |

### Rules

- ✅ Dashboard 3 calls run in parallel — `Promise.all()`
- ✅ If profile already in React state (navigating back) — do not re-fetch
- ✅ `/api/constants` called once at app start — never again
- ❌ Never call the same endpoint twice in a single page load
- ❌ Never chain calls sequentially when they can run in parallel
- ❌ Never fetch on every render — fetch on mount, store in state

---

## 8. Backend Efficiency Rules

| Rule | Detail |
|---|---|
| Routes are thin | No business logic in routes — all in `utils/` |
| No redundant DB reads | `user_id` from token — do not re-query `users/` to confirm existence |
| Suggestion engine after log update only | Never triggered on read requests |
| Gemini retry limit | 1 retry max — not an infinite loop |
| Gamification update async | Does not block chat-update response |
| Quiz generation cached | Check Firestore first — only call Gemini if no quiz exists for today |

### Response Size Rules

| Response | Rule |
|---|---|
| Chat update | Score, breakdown, analogy, delta, top 3 suggestions, streak — nothing else |
| Leaderboard | Top 50 — `rank`, `name` (first name only), `awareness_score`, `top_badge` |
| Weekly trend | 7 points — `date`, `daily_co2_kg` per entry |
| Profile | All fields — this call must be complete |
| Quiz | 3 questions, 4 options each, correct_index, explanation |
| Constants | Full `EMISSION_FACTORS` dict — served as-is |

---

## 9. Efficiency Checklist

**Constants**
- [ ] Emission numbers only in `emission_factors.py` — nowhere else
- [ ] `/api/constants` endpoint exists and is public
- [ ] Frontend loads constants once on app start — not per component

**Gemini**
- [ ] Can this be done with math? If yes — no Gemini
- [ ] Simulator touches Gemini? Should be zero
- [ ] Gemini call count ≤ 1 per user action (+ 1 retry)
- [ ] Quiz checks Firestore cache before calling Gemini

**Firestore**
- [ ] Document ID lookup available? Use it
- [ ] Non-indexed field in filter? Add index first
- [ ] `.limit()` on all list queries?
- [ ] Both indexes in `firestore.indexes.json`?

**Frontend**
- [ ] Slider debounced at 200ms?
- [ ] Page within API call budget?
- [ ] Parallel calls using `Promise.all()`?
- [ ] Constants loaded from module-level variable — not hardcoded?

**Simulator**
- [ ] Zero API calls during slider interaction?
- [ ] `simulate()` is pure and synchronous?
- [ ] No Apply button — "Log these changes" feeds into chat?

---

*EFFICIENCY.md Version 1.0 — Zerofy India*