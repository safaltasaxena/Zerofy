# Zerofy India — Coding Standards
> **Applies to:** All backend (Python/FastAPI) and frontend (React) code
> **Version:** 1.1
> **Rule:** If it isn't in this file, default to simplicity and readability over cleverness.

---

## 0. The Golden Rules

1. **Functions under 50 lines.** If it's growing beyond 50 — split it.
2. **Single responsibility.** Every function, file, and component does ONE thing.
3. **No god functions.** If you can't describe what it does in one sentence — split it.
4. **Proper separation.** Logic in utils. Routes thin. Components don't call Firestore. Frontend doesn't do math the backend should do — **exception: Simulator calculations are frontend math by design, using constants from `/api/constants`. See EFFICIENCY.md.**
5. **All code must be understandable and editable by someone who didn't write it.**

---

## 1. Python — Backend Standards

### 1.1 Naming

| Thing | Convention | Example |
|---|---|---|
| Variables and functions | `snake_case` | `daily_co2_kg`, `calculate_daily_score` |
| Constants | `UPPER_SNAKE_CASE` | `EMISSION_FACTORS`, `MAX_SUGGESTIONS` |
| Classes | `PascalCase` | `UserProfile`, `ParseFailedError` |
| Files | `snake_case` | `emission_factors.py`, `analogy_engine.py` |

### 1.2 Type Hints — Required on Every Function

```python
# ✅ Correct
def calculate_daily_score(profile: dict) -> float:
def get_analogy(co2_kg: float, context: str = "general") -> str:
def parse_user_message(message: str) -> dict:

# ❌ Wrong
def calculate_daily_score(profile):
```

### 1.3 Function Length — Max 50 Lines

If a function is approaching 50 lines — split before it crosses.

### 1.4 Error Handling — Every Function Has try/except

```python
# ✅ Correct
def calculate_daily_score(profile: dict) -> float:
    """Calculate total daily CO2 kg from user profile."""
    try:
        transport = get_transport_emission(profile["commute_mode"], profile["avg_daily_km"])
        diet = get_diet_emission(profile["diet_type"])
        electricity = get_electricity_emission(profile["ac_hours_per_day"])
        return round(transport + diet + electricity, 2)
    except KeyError as e:
        raise CalculationError(f"Missing required field: {e}")
    except Exception as e:
        raise CalculationError(f"Score calculation failed: {e}")

# ❌ Wrong — no error handling, no type hints, no docstring
def calculate_daily_score(profile):
    return EMISSION_FACTORS[profile["commute_mode"]] * profile["avg_daily_km"]
```

### 1.5 Custom Exceptions — Defined in the File They Belong To

```python
# utils/gemini_parser.py
class ParseFailedError(Exception):
    pass

class LowConfidenceError(Exception):
    pass

# utils/calculator.py
class CalculationError(Exception):
    pass
```

### 1.6 Docstrings — Required on Every Function

One-line minimum. No novels.

```python
def get_analogy(co2_kg: float, context: str = "general") -> str:
    """Convert a CO2 kg value into a human-readable analogy string."""
```

### 1.7 Constants File Rules

`emission_factors.py` is the **only** place numbers live. The `/api/constants` endpoint serves this dict to the frontend — no duplication anywhere.

```python
# ✅ Correct
EMISSION_FACTORS = {
    "transport": {
        "petrol_car": 0.17,        # kg CO2 per km
        "diesel_car": 0.15,        # kg CO2 per km
        "petrol_two_wheeler": 0.05,
        "electric_vehicle": 0.02,
        "auto_rickshaw": 0.07,
        "bus": 0.02,
        "metro": 0.01,
        "walking": 0.0,
        "cycling": 0.0,
    },
    ...
}

# ❌ Wrong — magic numbers in code
emission = 0.17 * km
```

### 1.8 Route Rules — Keep Routes Thin

Routes validate input, call utilities, return responses. No business logic in routes.

```python
# ✅ Correct — thin route
@router.post("/chat-update")
async def chat_update(body: ChatUpdateRequest, user_id: str = Depends(verify_token)):
    try:
        parsed = await gemini_parser.parse(body.message)
        updated_log = await log_service.update(user_id, parsed)
        analogy = analogy_engine.get_analogy(updated_log["delta_co2"])
        return {"success": True, "data": {"analogy": analogy, "log": updated_log}}
    except ParseFailedError:
        return {"success": False, "data": None, "error": "Could not understand message. Try the form below."}
    except Exception as e:
        logger.error(f"chat_update failed for {user_id}: {e}", exc_info=True)
        return {"success": False, "data": None, "error": "Something went wrong. Please try again."}
```

### 1.9 Response Format — Always Wrap

Every route must return the standard shape. No raw returns, no HTTP exceptions that bypass the wrapper.

```python
# ✅ Every response
return {"success": True,  "data": result, "error": None}
return {"success": False, "data": None,   "error": "Human-readable message"}

# ❌ Never
raise HTTPException(status_code=400, detail="bad input")  # bypasses format
return result                                               # raw return
```

### 1.10 Gemini Response Handling

Always clean Gemini output before parsing:

```python
# ✅ Correct
def clean_gemini_json(raw: str) -> dict:
    """Strip markdown fences and parse Gemini JSON response."""
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ParseFailedError("Gemini returned invalid JSON")
```

### 1.11 Imports — 3 Blocks

```python
# Block 1: Standard library
import os, json
from datetime import datetime

# Block 2: Third-party
from fastapi import APIRouter
from firebase_admin import firestore

# Block 3: Internal
from utils.calculator import calculate_daily_score
from constants.emission_factors import EMISSION_FACTORS
```

---

## 2. React — Frontend Standards

### 2.1 Styling — Tailwind CSS Only

No inline styles. No separate CSS files. Tailwind utility classes only.

```jsx
// ✅ Correct
<div className="flex flex-col gap-4 p-6 bg-white rounded-2xl shadow-md">

// ❌ Wrong
<div style={{ display: "flex", padding: "24px" }}>
import "./Dashboard.css"
```

### 2.2 Naming

| Thing | Convention | Example |
|---|---|---|
| Components | `PascalCase` | `ScoreBreakdown.jsx`, `ChatSection.jsx` |
| Functions inside components | `camelCase` | `handleSubmit`, `fetchDailyScore` |
| Props | `camelCase` | `dailyCo2`, `analogyText` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CHAT_LENGTH = 300` |

### 2.3 Component Structure — Always This Order

```jsx
// 1. Imports
import { useState, useEffect } from "react"
import { fetchUserProfile } from "../utils/api"

// 2. Named component function
export default function ScoreBreakdown({ userId, breakdown }) {

  // 3. State declarations
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 4. useEffect hooks
  useEffect(() => { ... }, [userId])

  // 5. Handler functions — all with try/catch
  const handleRefresh = async () => {
    try {
      setLoading(true)
      // ...
    } catch (err) {
      setError("Could not load your score. Please refresh.")
    } finally {
      setLoading(false)
    }
  }

  // 6. Pre-return logic — compute derived values here, not in JSX
  const transportPct = ((breakdown.transport / breakdown.total) * 100).toFixed(1)

  // 7. Early returns for loading/error
  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} />

  // 8. Main return — JSX only, no logic
  return (
    <div className="...">...</div>
  )
}
```

### 2.4 No Logic in JSX

```jsx
// ✅ Correct — logic before return
const scoreColor = dailyCo2 > 5 ? "text-red-500" : "text-green-500"
return <div className={scoreColor}>{dailyCo2.toFixed(2)} kg CO₂</div>

// ❌ Wrong — logic inside JSX
return <div className={dailyCo2 > 5 ? "text-red-500" : "text-green-500"}>...</div>
```

### 2.5 Emission Constants — From API, Not Hardcoded

```jsx
// ✅ Correct — loaded once from /api/constants on app start
import { getConstants } from "../utils/api"

// ❌ Wrong — hardcoded in frontend
const PETROL_CAR_FACTOR = 0.17
```

### 2.6 API Calls — Only Through `api.js`

```jsx
// ✅ Correct
import { getDailyScore } from "../utils/api"

// ❌ Wrong
const res = await fetch("http://localhost:8000/api/logs/today")
```

### 2.7 Props — Always Destructured

```jsx
// ✅ Correct
export default function ScoreBreakdown({ dailyCo2, breakdown, persona }) {

// ❌ Wrong
export default function ScoreBreakdown(props) {
  return <div>{props.dailyCo2}</div>
}
```

### 2.8 Error and Loading States — Required on Every Async Call

```jsx
// ✅ Correct
const fetchScore = async () => {
  try {
    setLoading(true)
    const data = await api.getDailyScore(userId)
    setScore(data.daily_co2_kg)
  } catch (err) {
    setError("Could not load your score. Please refresh.")
  } finally {
    setLoading(false)
  }
}

// ❌ Wrong — swallowed error
const fetchScore = async () => {
  const data = await api.getDailyScore(userId)
  setScore(data.daily_co2_kg)
}
```

---

## 3. File Size Limits

| File type | Limit |
|---|---|
| Python utility function | 50 lines per function |
| Python route file | 100 lines total |
| React component | 150 lines total |
| `api.js` | 200 lines total |
| `emission_factors.py` | No limit (data file) |

---

## 4. What Never Goes in Code

| Thing | Where instead |
|---|---|
| API keys | `.env` file |
| Emission numbers | `constants/emission_factors.py` only — served via `/api/constants` |
| Hardcoded user IDs | Never — always from session/state |
| `console.log` in production | Remove before commit |
| `print()` debug statements | Remove before commit |
| Commented-out dead code | Delete — Git history exists |
| TODO comments | Fine during dev — remove before submission |

---

## 5. Git Commit Standards

```
<type>: <short description>

feat:     new feature
fix:      bug fix
refactor: restructuring without behaviour change
test:     adding or fixing tests
docs:     README or MD changes
chore:    setup, config, dependencies

# Examples
feat: add calculator module with daily and monthly score functions
feat: add /api/constants endpoint serving emission factors
fix: handle missing diet_type in calculator
refactor: extract breakdown calculation into dedicated function
test: add unit tests for calculator module
chore: add firebase.py singleton with ADC + file path support
```

---

## 6. Quick Reference Checklist

**Python — before every commit:**
- [ ] Every function has type hints
- [ ] Every function has a docstring
- [ ] Every function has try/except
- [ ] No function over 50 lines
- [ ] No magic numbers — all in `emission_factors.py`
- [ ] Route is thin — logic is in utils
- [ ] Response is `{success, data, error}` — never raw
- [ ] Gemini response cleaned before `json.loads()`
- [ ] No API keys or secrets in code

**React — before every commit:**
- [ ] Tailwind only — no inline styles
- [ ] Every async call has try/catch
- [ ] Component under 150 lines
- [ ] No logic inside JSX return
- [ ] All API calls through `api.js`
- [ ] Emission constants from `/api/constants` — not hardcoded
- [ ] Props destructured
- [ ] Loading and error states handled

---

*CODING_STANDARDS.md Version 1.0 — Zerofy India*