# Zerofy India — Security Specification
**Stack:** Python (FastAPI) + React + Firestore + Gemini API | **Version:** 1.1
**Deployment:** Backend → GCP Cloud Run | Frontend → Vercel

---

## Core Principles

> **Never trust input.** Validate and sanitise everything — users, Gemini, Firestore.
> **Secrets never touch code.** API keys and credentials live in `.env` only.
> **Least privilege.** Every service and process gets only the permissions it needs.
> **Fail securely.** Log internally; return generic messages externally.
> **Defence in depth.** No single layer is the only defence — stack multiple controls.

---

## 1. HTTP Security Headers

**Location:** `backend/middleware/security_headers.py` — single middleware, not per-route.

| Header | Value | Attack Mitigated |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking via iframes |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | URL leakage to third parties |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Unwanted browser API access |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | Protocol downgrade attacks |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' https://generativelanguage.googleapis.com; frame-ancestors 'none'` | XSS, resource hijacking |

> **Note:** `style-src 'unsafe-inline'` required for Tailwind CSS.

---

## 2. CORS Configuration

**Location:** `backend/main.py`

| Parameter | Production Value | Rule |
|---|---|---|
| `allow_origins` | `https://zerofy.in, https://www.zerofy.in` | Exact origins only — no wildcards |
| `allow_methods` | `GET, POST, PUT` | Only methods the app uses |
| `allow_headers` | `Content-Type, Authorization` | No wildcard headers |
| `allow_credentials` | `true` | Required for auth |

- ✅ Origins loaded from `ALLOWED_ORIGINS` env variable
- ❌ Never `allow_origins=["*"]` in production

---

## 3. Rate Limiting

**Library:** `slowapi` | **Key function:** Remote IP address

| Endpoint | Limit | Reason |
|---|---|---|
| `POST /api/logs/chat-update` | 10 / min | Gemini cost protection |
| `POST /api/user/login` | 10 / min | Brute-force prevention |
| `POST /api/user/signup` | 5 / min | Signup spam prevention |
| `GET /api/quiz/today/{user_id}` | 30 / min | Normal usage |
| `GET /api/simulator/calculate` | 30 / min | Math only — generous |
| `GET /api/constants` | 60 / min | Public endpoint — generous |
| All other routes | 60 / min | Default ceiling |

---

## 4. Input Validation & Sanitisation

**Method:** Pydantic models on all request bodies.

### Field Constraint Matrix

| Field | Type | Constraint |
|---|---|---|
| `user_id` | `str` | `min=1`, `max=128` |
| `message` (chat) | `str` | `min=1`, `max=500`; HTML tags rejected |
| `name` | `str` | `min=1`, `max=100` |
| `state` / `city` | `str` | `min=2`, `max=50` |
| `avg_daily_km` | `float` | `0 ≤ x ≤ 500` |
| `monthly_electricity_units` | `float` | `0 ≤ x ≤ 10,000` |
| `ac_hours_per_day` | `float` | `0 ≤ x ≤ 24` |
| `lpg_cylinders_per_month` | `float` | `0 ≤ x ≤ 10` |
| `commute_mode` | `enum` | `petrol_car`, `diesel_car`, `petrol_two_wheeler`, `electric_vehicle`, `auto_rickshaw`, `bus`, `metro`, `walking`, `cycling` |
| `diet_type` | `enum` | `non_vegetarian`, `vegetarian`, `eggetarian`, `vegan` |
| `persona` | `enum` | `student`, `professional`, `family`, `teenager`, `senior` |

### Sanitisation Rules

- ✅ Strip whitespace from all string inputs
- ✅ Enum fields validated against allowlists
- ✅ HTML tags stripped from chat input
- ✅ Numeric fields capped at realistic maximums
- ❌ Never pass unsanitised input to Gemini
- ❌ Never use user input as Firestore document ID without validation

### Gemini Prompt Injection Prevention

```
User message → Emoji pre-processing → Truncate 500 chars → Strip/validate
      ↓
Insert into USER turn only — never into system prompt
      ↓
System prompt is static — instructs model to ignore behavioural instructions
      ↓
Gemini response → strip markdown fences → json.loads() → validate schema
```

---

## 5. Authentication

**Provider:** Firebase Authentication (JWT ID tokens)

### Token Verification Flow

```
User logs in via Firebase SDK
      ↓
Firebase returns ID Token (JWT, 1hr default)
      ↓
Frontend attaches to every request: Authorization: Bearer <token>
      ↓
Backend middleware verifies via Firebase Admin SDK
      ↓
Extracts uid → used as user_id in all routes
      ↓
Route receives user_id from Depends(verify_token) — never from request body
```

### Rules

| Rule | Behaviour |
|---|---|
| Source of `user_id` | Verified token `uid` only — never request body or query params |
| Endpoint coverage | Every non-public endpoint requires valid token |
| Public endpoints | `GET /api/constants` — no auth required |
| Token storage | Firebase ID token in memory only — **never** `localStorage` |
| `user_id` + `name` | May be stored in `localStorage` for display UX — never the token |
| Token logging | Never log tokens |
| Verification location | Middleware — not duplicated in routes |

---

## 6. Global Exception Handler

**Location:** `backend/exception_handler.py`

All unhandled exceptions — including FastAPI's own 422, 429, 413 — are intercepted and wrapped:

```
Any exception raised anywhere
      ↓
exception_handler.py catches it
      ↓
Logs full detail internally (logger.error with exc_info=True)
      ↓
Returns: { "success": false, "data": null, "error": "generic message" }
      ↓
No stack trace, no file path, no class name ever reaches the client
```

### Error Response Policy

| Scenario | External Response | Internal Action |
|---|---|---|
| Pydantic validation failure (422) | `"Please check your input and try again."` | `logger.warning` |
| Rate limit exceeded (429) | `"Too many requests. Please wait a moment."` | `logger.warning` |
| Payload too large (413) | `"Request too large."` | `logger.warning` |
| Parse / NLP failure | `"Couldn't understand that — try the form below."` | `logger.warning` |
| Auth failure (401) | `"Authentication failed."` | `logger.warning` |
| Unexpected exception (500) | `"Something went wrong. Please try again."` | `logger.error` with `exc_info=True` |

---

## 7. Container Security

### Dockerfile Rules

| Concern | Backend | Frontend |
|---|---|---|
| Base image | `python:3.11.9-slim` (pinned) | `node:20.12-alpine` → `nginx:1.25-alpine` |
| Runtime user | Non-root (`appuser`) | Non-root nginx |
| Tag strategy | Pinned exact version | Pinned exact version |

### Docker Compose Hardening

| Setting | Value | Purpose |
|---|---|---|
| `env_file` | `./backend/.env` | Secrets from file — never inline |
| `read_only` | `true` | Read-only filesystem |
| `tmpfs` | `/tmp` | Only writable location |
| `security_opt` | `no-new-privileges:true` | Block privilege escalation |
| `cap_drop` | `ALL` | Drop all Linux capabilities |
| `cap_add` | `NET_BIND_SERVICE` | Only what's needed |

- ❌ Never run containers as root
- ❌ Never use `latest` image tags

---

## 8. Environment Variables

### Variable Inventory

| Variable | File | Committed to Git? | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | `backend/.env` | ❌ No | — |
| `FIREBASE_PROJECT_ID` | `backend/.env` | ❌ No | Required in both local and GCP |
| `FIREBASE_CREDENTIALS_PATH` | `backend/.env` | ❌ No | Local dev only — omit on GCP |
| `ALLOWED_ORIGINS` | `backend/.env` | ❌ No | — |
| `ENVIRONMENT` | `backend/.env` | ❌ No | `development` or `production` |
| `RATE_LIMIT_STORAGE_URI` | `backend/.env` | ❌ No | — |
| `VITE_API_BASE_URL` | `frontend/.env` | ✅ Yes | No secrets |
| `VITE_API_BASE_URL` | `frontend/.env.production` | ✅ Yes | Points to Cloud Run URL |

### Firebase Init Logic

| Environment | Condition | Init Method |
|---|---|---|
| Local dev | `FIREBASE_CREDENTIALS_PATH` set | Credentials file |
| GCP Cloud Run | `FIREBASE_PROJECT_ID` set, no file path | Application Default Credentials |
| Neither set | Both missing | `RuntimeError` on startup |

### Rules

- ✅ `.env` always in `.gitignore`
- ✅ App fails to start if required secrets are missing
- ✅ `.env.example` committed with placeholder values only
- ✅ CI/CD secrets via GitHub Secrets — never in workflow files
- ❌ No secrets in source code, Dockerfiles, or `docker-compose.yml`

---

## 9. Firestore Security Rules

### Rule Matrix

| Collection | Read | Write | Document ID Pattern |
|---|---|---|---|
| `users/{userId}` | Owner only | Owner only | `userId` |
| `profiles/{userId}` | Owner only | Owner only | `userId` |
| `daily_logs/{logId}` | Authenticated, owns prefix | Authenticated, owns prefix | `{userId}_{date}` |
| `gamification/{userId}` | Owner only | **Backend only** (Admin SDK) | `userId` |
| `quiz_results/{resultId}` | Authenticated, owns prefix | Authenticated, owns prefix | `{userId}_{date}` |
| All other paths | ❌ Deny | ❌ Deny | — |

- Service account role: **Cloud Datastore User** only — not Owner or Editor
- Validate `user_id` length and format before any Firestore path construction

---

## 10. Middleware Stack

```
Incoming Request
      ↓
  [1] RateLimitMiddleware       ← First (innermost)
      ↓
  [2] RequestFilterMiddleware   ← Blocks path traversal, XSS probes
      ↓
  [3] RequestSizeLimitMiddleware ← 10KB max
      ↓
  [4] HTTPSRedirectMiddleware   ← Production only
      ↓
  [5] CORSMiddleware
      ↓
  [6] SecurityHeadersMiddleware ← Last (outermost)
      ↓
  Route Handler
      ↓
  exception_handler.py          ← Wraps all unhandled exceptions
```

### Additional Middleware

| Middleware | Parameter | Attack Mitigated |
|---|---|---|
| `RequestSizeLimitMiddleware` | Max 10 KB | Oversized payloads |
| `RequestFilterMiddleware` | Blocks `../`, `etc/passwd`, `<script`, `UNION SELECT`, `DROP TABLE` | Path traversal, injection probes |
| `HTTPSRedirectMiddleware` | HTTP → HTTPS when `ENVIRONMENT=production` | Plaintext traffic |

---

## 11. Transport Security

| Layer | Configuration |
|---|---|
| TLS protocols | 1.2 and 1.3 only |
| HSTS max-age | 63,072,000 seconds (2 years), `includeSubDomains` |
| HTTP → HTTPS | 301 redirect via nginx + middleware |
| Certificate | Let's Encrypt (auto-renewable) |

---

## 12. Bot Protection

| Layer | Mechanism | Targets |
|---|---|---|
| Firebase Auth (built-in) | Brute-force detection, anomaly detection | Credential stuffing |
| Rate limiting | 10/min login, 5/min signup | Volume attacks |
| Constant-time responses | `asyncio.sleep(0.3)` on failed login | Timing-based enumeration |
| Generic error messages | "Invalid email or password" — never "Email not found" | Account enumeration |
| Frontend honeypot | Hidden `<input name="website">` — bots fill it | Automated signup bots |

---

## 13. XSS Prevention

| Layer | Mechanism |
|---|---|
| React | JSX auto-escapes all rendered values |
| `dangerouslySetInnerHTML` | **Never used** |
| Backend output | Pure JSON — no HTML templates with user data |
| CSP header | `script-src 'self'` blocks injected scripts |

---

## 14. Data Protection

### Data Minimisation

| Data | Collected | Reason |
|---|---|---|
| Name | ✅ Yes | Personalisation |
| Email | ✅ Yes | Auth — Firebase managed |
| State / City | ✅ Yes | Leaderboard + suggestions |
| Habits | ✅ Yes | Core feature |
| Password | ❌ No | Firebase handles auth |
| GPS location | ❌ No | State/city sufficient |
| Device identifiers | ❌ No | Not needed |

### Retention Policy

| Collection | Retention |
|---|---|
| `daily_logs` | 90 days |
| `quiz_results` | 30 days |
| `gamification` | Indefinite |
| `users` / `profiles` | While account active |

### Logging Rules

- ✅ Log `user_id` only — not email, name, or habit data
- ❌ Never log tokens, passwords, or PII
- ❌ Never log habit data (health-adjacent)

---

## 15. Dependencies & CI/CD

### Automated Scanning

| Job | Tool | Trigger |
|---|---|---|
| Python scan | `safety check -r requirements.txt` | Every push / PR |
| Node scan | `npm audit --audit-level=high` | Every push / PR |
| Secret detection | `detect-secrets` (pre-commit) | Every commit |
| Python linting | `bandit -r backend/` (pre-commit) | Every commit |

### Version Pinning

- `requirements.txt`: exact versions — no `>=`, `~=`, `>`
- `package.json`: exact versions — no `^` or `~`

---

## 16. Pre-Deployment Checklist

**Authentication & Access**
- [ ] All non-public endpoints require valid Firebase token
- [ ] `GET /api/constants` is public — no auth
- [ ] `user_id` always from verified token
- [ ] Firestore rules deployed and tested
- [ ] Service account = Cloud Datastore User only

**Inputs & Outputs**
- [ ] All request bodies use Pydantic models
- [ ] Enum fields validated against allowlists
- [ ] Chat input stripped of HTML before Gemini
- [ ] Gemini response cleaned before `json.loads()`
- [ ] All error responses generic — no stack traces

**Transport & Headers**
- [ ] HTTPS enforced in production
- [ ] All security headers present
- [ ] CORS locked to specific origins
- [ ] HSTS set

**Secrets**
- [ ] `.env` in `.gitignore`
- [ ] No secrets in code, Dockerfiles, docker-compose
- [ ] App fails to start if `FIREBASE_PROJECT_ID` missing
- [ ] CI/CD uses masked variables

**Runtime**
- [ ] Containers non-root
- [ ] Rate limiting active
- [ ] Request size limit (10KB) active
- [ ] `exception_handler.py` registered in `main.py`
- [ ] No debug/print statements in production

---

*SECURITY_SPEC.md Version 1.0 — Zerofy India*