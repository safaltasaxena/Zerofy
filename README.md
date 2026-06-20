# 🌍 Zerofy

> A hyper-personalized carbon tracking and behavior change platform that empowers users to reduce their environmental impact through AI-driven insights, gamification, and interactive simulations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

---

## 📌 Problem Statement

People are largely unaware of their daily carbon footprint and how their habits contribute to climate change. Existing solutions are either too generic, require repetitive manual input, or fail to provide actionable, personalized insights that drive real behavioral change.

## 💡 Solution

Zerofy combines **real-time emissions tracking**, **AI-powered personalization**, and **gamified behavior change** to help users understand and reduce their environmental impact through data-driven insights and interactive simulations.

---

## 🚀 Key Features

### 🧠 Hyper-Personalized Insights
- AI-generated recommendations tailored to user's highest-impact habits
- Dynamic suggestions based on lifestyle patterns and historical behavior
- Actionable steps prioritized by carbon reduction potential

### 💬 Natural Language Chatbot
- Log activities conversationally—no forms, no friction
- AI auto-confirms and updates user data intelligently
- Seamless integration with carbon tracking system

### 📊 Carbon Score System
- Real-time daily carbon footprint calculations
- Visual breakdown by category (transport, food, energy, shopping, etc.)
- Weekly and monthly trend analysis with comparative insights

### 🔮 What-If Simulator
- Interactive sliders to predict carbon impact of lifestyle changes
- Visualize potential savings from switching habits
- Compare multiple scenarios side-by-side for informed decision-making

### 💧 Resource Awareness
- Track beyond carbon: water consumption, waste generation, resource usage
- Multi-dimensional environmental impact scoring
- Holistic sustainability view across all lifestyle areas

### 🧩 Interactive Quizzes
- Engaging educational quizzes on sustainable choices
- Real-time feedback and learning reinforcement
- Builds environmental awareness through gamified interactions

### 🏆 Gamification System
- Points earned for sustainable actions and habit streaks
- Global leaderboards for friendly competition
- Achievement badges and milestone celebrations
- Daily challenges to encourage consistent engagement

### 📈 Progress Tracking
- Historical trends and behavioral pattern analysis
- Measurable improvements over time with visual dashboards
- Goal setting, milestone tracking, and achievement systems
- Motivational insights to maintain momentum

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│              Frontend (Vercel / React)              │
│      React 18 + Vite + Recharts + Tailwind CSS     │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS / REST API
                     ▼
┌─────────────────────────────────────────────────────┐
│          Backend API (GCP Cloud Run)                │
│              FastAPI + Python 3.10+                 │
│                                                     │
│   ├─ Authentication Routes (Firebase)              │
│   ├─ Carbon Tracking & Calculation Engine          │
│   ├─ AI Insights & Personalization Service         │
│   ├─ What-If Simulator Logic                       │
│   ├─ Gamification & Leaderboard Service            │
│   └─ Data Validation & Rate Limiting               │
└────────────────────┬────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
┌──────────────────┐        ┌──────────────────┐
│  Firebase Auth   │        │  Firestore DB    │
│  + Security      │        │  Real-time Data  │
└──────────────────┘        └──────────────────┘
```

---

## 📂 Repository Structure

```
Zerofy/
├── frontend/                          # React + Vite application
│   ├── src/
│   │   ├── components/                # Reusable UI components
│   │   │   ├── CarbonScore/
│   │   │   ├── Chatbot/
│   │   │   ├── Simulator/
│   │   │   ├── Leaderboard/
│   │   │   └── ...
│   │   ├── pages/                     # Page-level components
│   │   ├── services/                  # API calls & Firebase integration
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── utils/                     # Helper functions
│   │   ├── styles/                    # Global styling
│   │   └── App.tsx
│   ├── tests/                         # Vitest unit & integration tests
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                           # FastAPI Python application
│   ├── routes/
│   │   ├── auth.py                    # Authentication endpoints
│   │   ├── carbon.py                  # Carbon tracking API
│   │   ├── insights.py                # AI insights generation
│   │   ├── simulator.py               # What-If simulation logic
│   │   ├── gamification.py            # Points & leaderboard
│   │   └── quiz.py                    # Quiz endpoints
│   ├── middleware/
│   │   ├── auth.py                    # JWT verification
│   │   ├── validation.py              # Input validation
│   │   └── security.py                # Security headers
│   ├── services/
│   │   ├── carbon_calculator.py       # Emissions calculation engine
│   │   ├── ai_insights.py             # LLM integration & insights
│   │   ├── user_service.py            # User data management
│   │   └── firebase_client.py         # Firebase integration
│   ├── models/                        # Pydantic data models
│   ├── tests/                         # Pytest unit & integration tests
│   ├── main.py                        # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docs/                              # Documentation & design specs
├── .github/
│   └── workflows/                     # CI/CD pipelines
├── .gitignore
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts | UI, visualization, bundling |
| **Backend** | FastAPI, Python 3.10+, Pydantic | API, business logic, validation |
| **Database** | Firebase Firestore, Auth | Real-time data, authentication |
| **AI/ML** | OpenAI API, Pandas, NumPy | Personalization, insights, analysis |
| **Deployment** | GCP Cloud Run, Vercel | Serverless hosting & scaling |
| **Testing** | Vitest, Pytest, axe-core | Unit, integration, accessibility tests |
| **DevOps** | Docker, GitHub Actions | Containerization, CI/CD automation |

---

## 🧪 Testing

All test suites pass successfully:

| Test Suite | Description | Status |
|-----------|-------------|--------|
| **Frontend Unit Tests** | Components, hooks, utilities (Vitest) | ✅ Passing |
| **Frontend Integration Tests** | User flows, simulator interactions | ✅ Passing |
| **Accessibility Tests** | ARIA compliance, keyboard nav (axe-core) | ✅ Passing |
| **Backend Unit Tests** | Route handlers, validators, logic (Pytest) | ✅ Passing |
| **Backend Integration Tests** | API endpoints, Firebase integration | ✅ Passing |
| **End-to-End Tests** | Complete user workflows | ✅ Passing |

**Run tests locally:**

```bash
# Frontend tests
cd frontend
npm run test

# Backend tests
cd backend
pytest tests/ -v
```

---

## 🔐 Security

- **Security Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Input Validation**: Strict Pydantic schema validation on all endpoints
- **Rate Limiting**: API endpoints protected against brute force and abuse
- **CORS Protection**: Cross-origin requests validated against whitelist
- **Authentication**: Firebase Auth with JWT token verification
- **Environment Variables**: Sensitive credentials managed via `.env` (never committed)
- **Data Encryption**: HTTPS enforced for all traffic
- **SQL Injection Prevention**: Parameterized Firestore queries only

---

## ♿ Accessibility

- **Semantic HTML**: Proper heading hierarchy, landmark regions, semantic elements
- **ARIA Labels**: Descriptive labels and live regions for screen readers
- **Keyboard Navigation**: Full keyboard support for all interactive elements
- **Color Contrast**: WCAG AA compliant text contrast (4.5:1 minimum)
- **Focus Management**: Visible focus indicators throughout application
- **Automated Testing**: axe-core ensures ongoing WCAG compliance

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ & npm
- **Python** 3.10+ & pip
- **Firebase** project (free tier available)
- **Google Cloud** account (for deployment)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access at `http://localhost:5173`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate     # macOS/Linux
# or
venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Access API at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

### Environment Configuration

**Frontend** (`.env.local`):
```env
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_id
VITE_FIREBASE_APP_ID=your_app_id
```

**Backend** (`.env`):
```env
ENVIRONMENT=development
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_key
FIREBASE_CLIENT_EMAIL=your_email
OPENAI_API_KEY=your_key
CORS_ORIGINS=http://localhost:5173
```

---

## 🚀 Deployment

### Frontend Deployment (Vercel)

1. Connect GitHub repository to [Vercel](https://vercel.com)
2. Configure environment variables in Vercel dashboard
3. Deploy automatically on push to `main` branch

```bash
npm install -g vercel
vercel --prod
```

### Backend Deployment (GCP Cloud Run)

1. Set up Google Cloud project and enable Cloud Run API
2. Build and push container:

```bash
gcloud auth configure-docker
docker build -t gcr.io/YOUR_PROJECT_ID/zerofy-backend .
docker push gcr.io/YOUR_PROJECT_ID/zerofy-backend
```

3. Deploy to Cloud Run:

```bash
gcloud run deploy zerofy-backend \
  --image gcr.io/YOUR_PROJECT_ID/zerofy-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,FIREBASE_PROJECT_ID=your_id
```

---

## 📊 Performance Targets

- **Frontend Load Time**: < 2s (optimized with code splitting & lazy loading)
- **API Response Time**: < 500ms (p95 latency)
- **Carbon Calculation Accuracy**: ≥ 98% vs EPA standards
- **Uptime SLA**: 99.9%
- **Lighthouse Score**: 90+

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please ensure all tests pass before submitting a PR.

---

## 📧 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/safaltasaxena/Zerofy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/safaltasaxena/Zerofy/discussions)
- **Email**: safaltasaxena7@gmail.com

---

Made with ❤️ for a sustainable future

</div>
