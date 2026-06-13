# Zerofy India — Testing Specification
**Stack:** Python (FastAPI) + React + Firestore + Gemini API | **Version:** 1.1

---

## Core Principles

> **Test behaviour, not implementation.**
> **No real AI or Firebase calls in tests — always mocked.**
> **Every test must be deterministic — same result every run.**
> **Test files mirror source files.**

---

## Testing Stack

| Layer | Tool | Purpose |
|---|---|---|
| Backend unit + integration | `pytest` | All Python tests |
| Async route testing | `pytest-asyncio` + `httpx.AsyncClient` | FastAPI endpoint tests |
| Mocking | `pytest-mock` / `unittest.mock` | Isolate Gemini, Firebase |
| Frontend components | `Vitest` + `@testing-library/react` | React component tests |
| Accessibility | `axe-core` via `@axe-core/react` | ARIA, contrast, keyboard |
| Schema validation | `pydantic` + `pytest` | Request/response shape |

---

## Test File Map

| Source File | Test File | Type |
|---|---|---|
| `constants/emission_factors.py` | `tests/test_constants.py` | Unit |
| `utils/calculator.py` | `tests/test_calculator.py` | Unit |
| `utils/analogy_engine.py` | `tests/test_analogies.py` | Unit |
| `utils/gemini_parser.py` | `tests/test_gemini_parser.py` | Unit (mocked) |
| `utils/suggestion_engine.py` | `tests/test_suggestions.py` | Unit (mocked) |
| `routes/user.py` | `tests/test_routes_user.py` | Integration |
| `routes/logs.py` | `tests/test_routes_logs.py` | Integration |
| `routes/simulator.py` | `tests/test_routes_simulator.py` | Integration |
| `routes/quiz.py` | `tests/test_routes_quiz.py` | Integration |
| `routes/gamification.py` | `tests/test_routes_gamification.py` | Integration |
| `routes/constants.py` | `tests/test_routes_constants.py` | Integration |
| `config/firebase.py` | `tests/test_firebase.py` | Unit (mocked) |
| `middleware/auth.py` | `tests/test_security.py` | Unit |
| `middleware/rate_limiter.py` | `tests/test_security.py` | Unit (SEC-06–08) |
| `exception_handler.py` | `tests/test_exception_handler.py` | Unit |
| `src/utils/api.js` | `src/__tests__/api.test.js` | Unit |

---

## 1. Schema Validation Tests

**File:** `tests/test_schema_validation.py`

### Request Schema Tests

| Test ID | Model | Input | Expected |
|---|---|---|---|
| `SV-01` | `OnboardingRequest` | All valid fields | Passes |
| `SV-02` | `OnboardingRequest` | `avg_daily_km = 501` | `ValidationError` |
| `SV-03` | `OnboardingRequest` | `avg_daily_km = -1` | `ValidationError` |
| `SV-04` | `OnboardingRequest` | `commute_mode = "helicopter"` | `ValidationError` |
| `SV-05` | `OnboardingRequest` | `diet_type = "carnivore"` | `ValidationError` |
| `SV-06` | `OnboardingRequest` | `user_id = ""` | `ValidationError` |
| `SV-07` | `OnboardingRequest` | `user_id` = 200-char string | `ValidationError` |
| `SV-08` | `OnboardingRequest` | `ac_hours_per_day = 25` | `ValidationError` |
| `SV-09` | `OnboardingRequest` | `lpg_cylinders_per_month = 11` | `ValidationError` |
| `SV-10` | `ChatUpdateRequest` | `message = "<script>alert(1)</script>"` | `ValidationError` |
| `SV-11` | `ChatUpdateRequest` | `message = " "` | `ValidationError` after strip |
| `SV-12` | `ChatUpdateRequest` | `message` = 501-char string | `ValidationError` |
| `SV-13` | `OnboardingRequest` | `monthly_electricity_units = 10001` | `ValidationError` |
| `SV-14` | `OnboardingRequest` | `persona = "retiree"` | `ValidationError` |
| `SV-15` | `OnboardingRequest` | `commute_mode = "diesel_car"` | Passes — valid enum value |

### Response Schema Tests

| Test ID | Scenario | Expected Shape |
|---|---|---|
| `SV-16` | Any success | `{success: true, data: {...}, error: null}` |
| `SV-17` | Any failure | `{success: false, data: null, error: "string"}` |
| `SV-18` | FastAPI 422 | Wrapped in standard format — not raw FastAPI response |
| `SV-19` | FastAPI 429 | Wrapped — `"Too many requests. Please wait a moment."` |
| `SV-20` | FastAPI 413 | Wrapped — `"Request too large."` |
| `SV-21` | Any error | `error` is generic string — no stack trace, no file path |

---

## 2. i18n / India-Localisation Tests

**File:** `tests/test_i18n.py`

### Emission Factor Tests

| Test ID | Assertion | Expected Value |
|---|---|---|
| `I18N-01` | `EMISSION_FACTORS["electricity"]["grid_factor"]` | `0.82` (CEA India) |
| `I18N-02` | `EMISSION_FACTORS["transport"]["petrol_car"]` | `0.17` |
| `I18N-02b` | `EMISSION_FACTORS["transport"]["diesel_car"]` | `0.15` |
| `I18N-03` | `EMISSION_FACTORS["transport"]["petrol_two_wheeler"]` | `0.05` |
| `I18N-04` | `EMISSION_FACTORS["transport"]["auto_rickshaw"]` | `0.07` |
| `I18N-05` | `EMISSION_FACTORS["transport"]["metro"]` | `0.01` |
| `I18N-06` | `EMISSION_FACTORS["lpg"]["kg_co2_per_cylinder"]` | `12.0` |
| `I18N-07` | `EMISSION_FACTORS["diet"]["non_vegetarian"]` | `5.0` |

### Commute & Diet Coverage

| Test ID | Assertion | Expected |
|---|---|---|
| `I18N-08` | `auto_rickshaw` in enum | Present |
| `I18N-09` | `diesel_car` in enum | Present |
| `I18N-10` | `walking` and `cycling` → 0 kg | `calculate_daily_score` returns diet-only for these |
| `I18N-11` | `eggetarian` in diet enum | Present |
| `I18N-12` | `eggetarian` score between veg and non-veg | `2.5 < x < 5.0` |
| `I18N-13` | `vegan < vegetarian < eggetarian < non_vegetarian` | Ordering correct |

### Persona Coverage

| Test ID | Assertion | Expected |
|---|---|---|
| `I18N-14` | All 5 personas in allowlist | `student`, `professional`, `family`, `teenager`, `senior` |
| `I18N-15` | Student suggestions reference campus/canteen | String contains relevant keyword |
| `I18N-16` | Family suggestions reference LPG or household | String contains relevant keyword |

### Analogy Localisation

| Test ID | Assertion | Expected |
|---|---|---|
| `I18N-17` | 1 kg analogy references smartphones or ceiling fan | No "miles" or non-India units |
| `I18N-18` | Distance in km — never miles | No "mile" substring in any output |

### Constants Endpoint

| Test ID | Assertion | Expected |
|---|---|---|
| `I18N-19` | `GET /api/constants` returns full `EMISSION_FACTORS` dict | All keys present |
| `I18N-20` | `/api/constants` response matches `emission_factors.py` exactly | Deep equality check |

---

## 3. Utility Tests

### 3a. Calculator (`tests/test_calculator.py`)

| Test ID | Function | Input | Expected |
|---|---|---|---|
| `CALC-01` | `calculate_daily_score` | `petrol_car`, 10km, non-veg, 2 AC hours | `0.17×10 + 5.0 + 0.82×1.5×2 = 9.16 kg` |
| `CALC-02` | `calculate_daily_score` | `walking`, 0km, vegan, 0 AC | `1.5 kg` |
| `CALC-03` | `calculate_daily_score` | `metro`, 8km, vegetarian, 0 AC | `0.01×8 + 2.5 = 2.58 kg` |
| `CALC-04` | `calculate_daily_score` | `diesel_car`, 10km, non-veg, 0 AC | `0.15×10 + 5.0 = 6.5 kg` |
| `CALC-05` | `calculate_monthly_score` | daily=5.0 | `150.0 kg` |
| `CALC-06` | `calculate_delta` | old=8.16, new=2.58 | `-5.58 kg` (saving) |
| `CALC-07` | `calculate_delta` | old=2.58, new=8.16 | `+5.58 kg` (increase) |
| `CALC-08` | `calculate_breakdown` | `petrol_car` 10km, non-veg, 2 AC hours | Returns dict with `transport`, `diet`, `electricity`, `lpg` keys summing to total |
| `CALC-09` | `simulate_changes` (backend) | Switch car → metro, 10km | Score reduced by `(0.17-0.01)×10 = 1.6 kg` |
| `CALC-10` | `calculate_daily_score` | Missing `commute_mode` | Raises `CalculationError` |
| `CALC-11` | `calculate_daily_score` | `avg_daily_km = 0` | No error — valid result |
| `CALC-12` | Return precision | Any valid input | Rounded to 2 decimal places |

### 3b. Analogy Engine (`tests/test_analogies.py`)

| Test ID | Input | Expected |
|---|---|---|
| `ANA-01` | `1.0` kg | Contains "121 smartphone" or "ceiling fan" reference |
| `ANA-02` | `0.0` kg | Returns zero-state message — no crash |
| `ANA-03` | `100.0` kg | Returns scaled analogy |
| `ANA-04` | Negative value | Returns `CalculationError` or zero-clamps |
| `ANA-05` | `1.0` kg, `context="transport"` | Returns transport-specific analogy |
| `ANA-06` | Negative value | Returns `CalculationError` or zero-clamps |
| `ANA-07` | Return type — any valid input | Always returns `str` — never `None` |
| `ANA-08` | No external calls — any input | No DB or API calls made (pure function) |

### 3c. Suggestion Engine (`tests/test_suggestions.py`)

| Test ID | Scenario | Expected |
|---|---|---|
| `SUG-01` | `petrol_car` 20km/day | First suggestion addresses transport |
| `SUG-02` | `metro` 5km/day | Transport suggestion NOT returned |
| `SUG-03` | `non_vegetarian` user | Suggestion to reduce meat |
| `SUG-04` | `ac_hours_per_day = 8` | AC reduction suggested |
| `SUG-05` | Any valid profile | Exactly 3 suggestions — never more |
| `SUG-06` | `student` persona | Suggestion references campus/canteen |
| `SUG-07` | Gemini unavailable | Falls back to raw rule-based templates |
| `SUG-08` | Already-dismissed suggestion | Dismissed ID in exclusion list — that suggestion not returned |

---

## 4. Constants Tests

**File:** `tests/test_constants.py`

| Test ID | Assertion | Expected |
|---|---|---|
| `CONST-01` | `EMISSION_FACTORS` is a `dict` | `isinstance(EMISSION_FACTORS, dict)` |
| `CONST-02` | All 4 top-level categories present | `transport`, `diet`, `electricity`, `lpg` |
| `CONST-03` | All 9 transport modes present | Includes `diesel_car` |
| `CONST-04` | All 4 diet types present | `non_vegetarian`, `vegetarian`, `eggetarian`, `vegan` |
| `CONST-05` | All values are `float` or `int` | No strings in values |
| `CONST-06` | All emission values ≥ 0 | No negatives |
| `CONST-07` | `walking` and `cycling` = 0 | Exact value check |
| `CONST-08` | `grid_factor` in range | `0.7 ≤ x ≤ 1.0` |
| `CONST-09` | `petrol_car > electric_vehicle` | Ordering correct |
| `CONST-10` | `non_vegetarian > vegan` | Ordering correct |
| `CONST-11` | No duplicate keys | Key collision check |
| `CONST-12` | No side effects on import | No function calls at import |
| `CONST-13` | `GET /api/constants` response == `EMISSION_FACTORS` | Deep equality |

---

## 5. Logger Tests

**File:** `tests/test_logger.py`

| Test ID | Scenario | Assertion |
|---|---|---|
| `LOG-01` | Login logged | `user_id` in output |
| `LOG-02` | Login logged | Email NOT in output |
| `LOG-03` | Login logged | Password NOT in output |
| `LOG-04` | Token in request | Token string NOT logged |
| `LOG-05` | Chat update | Habit values NOT logged |
| `LOG-06` | Parse failure | `WARNING` level |
| `LOG-07` | Unexpected exception | `ERROR` level with `exc_info=True` |
| `LOG-08` | Successful request | `INFO` level |
| `LOG-09` | Gemini response | Raw response NOT logged |
| `LOG-10` | External error response | Internal error detail NOT forwarded to client response |

---

## 6. Firebase & AI (Mocked) Tests

### 6a. Firebase (`tests/test_firebase.py`)

| Test ID | Scenario | Condition | Assertion |
|---|---|---|---|
| `FB-01` | First `get_db()` call | Normal | Returns Firestore client |
| `FB-02` | `get_db()` called twice | Normal | Same instance — not reinitialised |
| `FB-03` | Local dev — credentials file | `FIREBASE_CREDENTIALS_PATH` set | Initialises using file |
| `FB-03b` | GCP production | `FIREBASE_PROJECT_ID` set, no file | Initialises using ADC |
| `FB-03c` | Neither set | Both missing | Raises `RuntimeError` |
| `FB-04` | `get_user_profile` — exists | Mock returns doc | Returns correct dict |
| `FB-05` | `get_user_profile` — not found | Mock returns nothing | Raises `ProfileNotFoundError` |
| `FB-06` | `user_id` > 128 chars | — | Raises `ValueError` before Firestore |
| `FB-07` | Write succeeds | Mock confirms | Returns success |
| `FB-08` | Write fails | Mock raises exception | Raises `DatabaseError` |

### 6b. Gemini Parser (`tests/test_gemini_parser.py`)

| Test ID | Scenario | Mock Response | Assertion |
|---|---|---|---|
| `GEM-01` | Valid message | Clean JSON | Returns dict with all required keys |
| `GEM-02` | Low confidence | `confidence: "low"` | Raises `LowConfidenceError` |
| `GEM-03` | Malformed JSON | `"not json"` | Strips fences, retries, then `ParseFailedError` |
| `GEM-04` | JSON wrapped in ```json fences | ` ```json {...} ``` ` | Fences stripped — parses successfully |
| `GEM-05` | Timeout | Raises `TimeoutError` | Raises `ParseFailedError` |
| `GEM-06` | First fails, retry succeeds | Fail then succeed | Returns valid result |
| `GEM-07` | Both retries fail | Fail twice | `ParseFailedError` after 2 attempts |
| `GEM-08` | Prompt injection attempt | "ignore all instructions" | Truncated — placed in user turn only |
| `GEM-09` | Message > 500 chars | 600-char string | Truncated to 500 before API call |
| `GEM-10` | Emoji in message | "took 🚇 today" | Emoji pre-processed to "metro" before Gemini |
| `GEM-11` | Valid response | Normal | `call_count == 1` |

### 6c. Exception Handler (`tests/test_exception_handler.py`)

| Test ID | Scenario | Expected |
|---|---|---|
| `EXC-01` | Unhandled `Exception` raised in route | Returns `{success: false, data: null, error: "Something went wrong..."}` |
| `EXC-02` | FastAPI 422 validation error | Wrapped in standard format |
| `EXC-03` | Rate limit 429 | Wrapped — generic message |
| `EXC-04` | Any error | Response never contains stack trace |
| `EXC-05` | Any error | `logger.error` called with `exc_info=True` |

---

## 7. Component Tests (Frontend)

**Tools:** `Vitest` + `@testing-library/react` | All `api.js` functions mocked via `vi.mock`

| Test ID | Component | Scenario | Assertion |
|---|---|---|---|
| `COMP-01` | `ScoreBreakdown` | `breakdown = {transport:1.7, diet:5.0, electricity:1.46, lpg:0}` | Pie chart renders 4 slices |
| `COMP-02` | `ScoreBreakdown` | Renders with analogy | Analogy string visible |
| `COMP-03` | `SimulatorSection` | Slider moved | `simulate()` called — no API call |
| `COMP-04` | `SimulatorSection` | Slider moved | `SimulatorBreakdown` pie updates |
| `COMP-05` | `SimulatorSection` | No Apply button | Button with text "Apply" does not exist in DOM |
| `COMP-06` | `SimulatorSection` | "Log these changes" clicked | Chat input pre-filled |
| `COMP-07` | `ChatSection` | User submits message | `api.submitChatUpdate` called |
| `COMP-08` | `ChatSection` | API returns fallback flag | `QuickUpdateForm` rendered |
| `COMP-09` | `ChatSection` | Bot response shown | Response text visible — natural language not "parsed: transport" |
| `COMP-10` | `ParsePreview` | Valid parse | Shows category, change, value before confirm |
| `COMP-11` | `ParsePreview` | Confirm clicked | `api.confirmChatUpdate` called |
| `COMP-12` | `ParsePreview` | Edit clicked | `QuickUpdateForm` shown |
| `COMP-13` | `OnboardingForm` | Honeypot field filled | Submission silently cancelled |
| `COMP-14` | `OnboardingForm` | `avg_daily_km = 999` | Validation error shown |
| `COMP-15` | `DailyQuiz` | Correct answer | Score updates + encouragement |
| `COMP-16` | `DailyQuiz` | Wrong answer | Correct revealed + explanation |
| `COMP-17` | `DailyQuiz` | Already completed today | Quiz locked — cannot re-submit |
| `COMP-18` | `StreakCounter` | `log_streak = 0` | Renders without crash |
| `COMP-19` | `BadgeShelf` | Empty badges | Renders empty state — no crash |
| `COMP-20` | `WeeklyChart` | 7 days of data | Recharts renders 7 data points |

---

## 8. Security Tests

**File:** `tests/test_security.py`

### Authentication

| Test ID | Scenario | Expected |
|---|---|---|
| `SEC-01` | No token | `401` |
| `SEC-02` | Expired token | `401` |
| `SEC-03` | Malformed token | `401` |
| `SEC-04` | Valid token, body `user_id` differs | Route uses token `uid` — body ignored |
| `SEC-05` | `GET /api/constants` — no token | `200` — public endpoint |

### Rate Limiting

| Test ID | Endpoint | Scenario | Expected |
|---|---|---|---|
| `SEC-06` | `POST /api/logs/chat-update` | 11 requests/min | 11th returns `429` wrapped in standard format |
| `SEC-07` | `POST /api/user/login` | 11 requests/min | 11th returns `429` |
| `SEC-08` | `POST /api/user/signup` | 6 requests/min | 6th returns `429` |

### Input Sanitisation

| Test ID | Input | Expected |
|---|---|---|
| `SEC-09` | `message = "<script>alert(1)</script>"` | `422` wrapped |
| `SEC-10` | URL with `../etc/passwd` | `400` |
| `SEC-11` | URL with `UNION SELECT` | `400` |
| `SEC-12` | Payload > 10KB | `413` wrapped |

### Security Headers

| Test ID | Header | Expected |
|---|---|---|
| `SEC-13` | `X-Content-Type-Options` | `nosniff` |
| `SEC-14` | `X-Frame-Options` | `DENY` |
| `SEC-15` | `Content-Security-Policy` | Contains `default-src 'self'` |
| `SEC-16` | `Strict-Transport-Security` | Contains `max-age=63072000` |
| `SEC-17` | `X-Frame-Options` | `DENY` |
| `SEC-18` | `Content-Security-Policy` | Contains `default-src 'self'` |
| `SEC-19` | `Strict-Transport-Security` | Contains `max-age=63072000` |
| `SEC-20` | `Referrer-Policy` | `strict-origin-when-cross-origin` |

### Error Response Hygiene

| Test ID | Trigger | Expected |
|---|---|---|
| `SEC-21` | Force internal exception | Response `error` field is generic string |
| `SEC-22` | Force internal exception | Response does NOT contain file path, line number, or class name |
| `SEC-23` | Invalid Firestore ID | `400` returned — Firestore path not exposed in response |

---

## 9. Accessibility Tests

**File:** `src/__tests__/accessibility.test.jsx`

| Test ID | Component | Assertion |
|---|---|---|
| `A11Y-01` | `OnboardingForm` | All inputs have `<label>` or `aria-label` |
| `A11Y-02` | `OnboardingForm` | Tab order follows visual order |
| `A11Y-03` | `ChatSection` | Input keyboard-accessible |
| `A11Y-04` | `SimulatorSection` | Sliders operable via arrow keys |
| `A11Y-05` | `ScoreBreakdown` | Pie chart has `role="img"` + `aria-label` with all slice values |
| `A11Y-06` | Loading states | `aria-busy="true"` during API calls |
| `A11Y-07` | Error messages | `role="alert"` on error containers |
| `A11Y-08` | `StreakCounter` | Fire emoji `aria-hidden="true"` |
| `A11Y-09` | All tap targets | Minimum 44×44px |
| `A11Y-10` | Colour contrast | All text passes WCAG AA (≥4.5:1) |
| `A11Y-11` | `DailyQuiz` | Quiz locked message visible when already completed |

---

## 10. Edge Case Tests

### Calculator

| Test ID | Scenario | Expected |
|---|---|---|
| `EDGE-01` | `avg_daily_km = 0` | Valid result — no division error |
| `EDGE-02` | `ac_hours_per_day = 0` | Electricity = 0 |
| `EDGE-03` | All zero habits | Diet-only score — not 0 |
| `EDGE-04` | Max values (km=500, ac=24, lpg=10) | Large but valid float |
| `EDGE-05` | `calculate_delta` — no change | Returns `0.0` exactly |
| `EDGE-06` | Unknown `commute_mode` | Raises `CalculationError` — not silent default |

### Gemini Parser

| Test ID | Scenario | Expected |
|---|---|---|
| `EDGE-07` | Empty string | `ParseFailedError` before API call |
| `EDGE-08` | Whitespace only | `ParseFailedError` after strip |
| `EDGE-09` | Hindi/mixed language | Passed to Gemini — low confidence — fallback |
| `EDGE-10` | Extra keys in response | Extra keys ignored — schema keys only |
| `EDGE-11` | Array instead of object | `ParseFailedError` |
| `EDGE-12` | Emoji-only message "🚇" | Pre-processed to "metro" — valid parse |

### Firestore

| Test ID | Scenario | Expected |
|---|---|---|
| `EDGE-13` | Daily log already exists for today | Overwritten — not duplicated |
| `EDGE-14` | Non-existent user profile | `ProfileNotFoundError` — not `KeyError` |
| `EDGE-15` | `user_id` with special characters | `ValueError` before Firestore path construction |
| `EDGE-16` | Empty `gamification` doc | All fields default to 0 |

### Quiz

| Test ID | Scenario | Expected |
|---|---|---|
| `EDGE-17` | Quiz already taken today | Returns stored result — no new Gemini call |
| `EDGE-18` | Gemini fails to generate quiz | Returns generic fallback questions |
| `EDGE-19` | No log data for user yet | Quiz generated from profile baseline |

### Frontend

| Test ID | Scenario | Expected |
|---|---|---|
| `EDGE-20` | `ScoreBreakdown` all values zero | Renders empty state — no divide by zero |
| `EDGE-21` | Leaderboard — user rank 1 | Displays "1st" — no layout break |
| `EDGE-22` | Leaderboard — user not ranked | Shows placeholder — no crash |
| `EDGE-23` | Form double-submit | Second blocked by `isLoading` guard |
| `EDGE-24` | API returns `success: false, data: null` | Error shown — no `null.field` crash |
| `EDGE-25` | `/api/constants` fails on app start | App shows error state — does not silently use undefined constants |

---

## 11. CI/CD Integration

**Platform:** GitHub Actions

### Workflow: `security.yml` — runs on every push and PR

| Job | Steps |
|---|---|
| `python-audit` | Checkout → Python 3.11 → `pip install safety` → `safety check -r backend/requirements.txt` |
| `node-audit` | Checkout → Node 20 → `npm ci` → `npm audit --audit-level=high` |

### Workflow: `test.yml` — runs on every push and PR

| Job | Steps |
|---|---|
| `backend-tests` | Checkout → Python 3.11 → `pip install -r requirements.txt` → `pytest backend/tests/ --cov=backend --cov-report=xml` |
| `frontend-tests` | Checkout → Node 20 → `npm ci` → `npx vitest run` |

### Pre-commit Hooks (`.pre-commit-config.yaml`)

| Hook | Tool | Purpose |
|---|---|---|
| Secret detection | `detect-secrets` | Blocks commits with credentials |
| Python linting | `bandit -r backend/` | Catches insecure patterns |

---

## What NOT to Test

| Category | Reason |
|---|---|
| Tailwind class names | Tailwind's responsibility |
| Firebase Admin SDK internals | Already tested by Google — mock the interface |
| Gemini API responses | Non-deterministic — test your parsing only |
| Python stdlib (`datetime`, `os`, `re`) | Trust the stdlib |
| Exact Gemini wording | Non-deterministic — test structure only |
| `/api/constants` values change | They don't at runtime — test on import |

---

## Run Commands

| Command | What it runs |
|---|---|
| `pytest backend/tests/` | All backend tests |
| `pytest -k "SEC"` | Security tests only |
| `pytest -k "CALC"` | Calculator tests only |
| `pytest --cov=backend --cov-report=term` | Coverage report |
| `npx vitest run` | All frontend tests |
| `npx vitest run --reporter=verbose` | Frontend with full output |

---

## Pass Criteria

| Metric | Minimum |
|---|---|
| Backend unit pass rate | 100% |
| Backend coverage — `utils/` | ≥ 90% |
| Backend coverage — `routes/` | ≥ 80% |
| Frontend component pass rate | 100% |
| Security tests | 100% — zero tolerance |
| Accessibility violations (`axe`) | 0 critical, 0 serious |

---

*TESTING.md Version 1.0 — Zerofy India*