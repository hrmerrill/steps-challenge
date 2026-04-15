# Copilot Instructions — Steps Challenge

## Project Overview

This is a **Steps Challenge** webapp for group step competitions. Monthly challenges where
participants track daily steps via fitness tracker sync (Garmin, Strava, Fitbit) or manual entry.
Features a leaderboard, "miles clubs" (tiers based on prior month steps), and a virtual trail map
showing collective progress.

## Architecture

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic / PostgreSQL
- **Frontend:** TypeScript / Vite / Leaflet.js — vanilla TS, no framework
- **Testing:** pytest (backend) + Vitest (frontend) — always include tests with changes
- **CI:** GitHub Actions runs both test suites on every push and PR

## Directory Layout

```
backend/          Python API server
  app/
    main.py       FastAPI app + CORS + health check
    config.py     Pydantic settings (env vars)
    database.py   SQLAlchemy engine + session + Base
    models/       ORM models (User, DailySteps, Challenge, ChallengeParticipant)
    routers/      API route modules (auth, steps, leaderboard, challenges)
    services/     Business logic (sync, miles_clubs, trail)
    schemas/      Pydantic request/response schemas
  tests/          pytest tests — mirrors app/ structure
  alembic/        Database migrations

frontend/         TypeScript SPA
  src/
    main.ts       App entry point
    api.ts        API client with JWT auth
    pages/        Page components (landing, login, register, profile, log-steps)
    components/   Reusable components (leaderboard, trail-map, miles-club, step-chart, nav)
    styles/       CSS (global vars, card system, component styles)
  tests/          Vitest tests
```

## Coding Conventions

### Backend (Python)
- Use **type hints** everywhere — Pydantic models for request/response schemas
- Follow **PEP 8** via Ruff (config in pyproject.toml)
- Database sessions via FastAPI dependency injection (`get_db`)
- All routes go in `routers/` and get included in `main.py`
- Business logic in `services/` — routers should be thin
- Tests use in-memory SQLite (see `tests/conftest.py`) — no PostgreSQL needed to run tests

### Frontend (TypeScript)
- **No framework** — vanilla TypeScript with DOM APIs
- Styles in CSS files using CSS custom properties (see `styles/global.css` for design tokens)
- Card-based UI layout (see `styles/cards.css`)
- API calls through `api.ts` — handles JWT tokens automatically
- Tests in `tests/` directory using Vitest + jsdom

### General
- **Always write unit tests** when adding or changing functionality
- Keep functions small and focused
- Use descriptive variable names
- Document public APIs with JSDoc (TS) or docstrings (Python)

## Key Patterns

### Miles Clubs
Tiers assigned at challenge start based on previous month's total steps:
- 🥇 Gold: 300,000+ steps/month
- 🥈 Silver: 200,000+ steps/month
- 🥉 Bronze: 100,000+ steps/month

Thresholds are configurable via environment variables.

### Virtual Trail Map
- Leaflet.js with OpenStreetMap tiles
- Convert total group steps → miles (2,000 steps/mile) → position on trail GeoJSON
- Appalachian Trail is the default route

### Auth Flow
- Email/password registration → bcrypt hash → JWT token
- JWT passed via `Authorization: Bearer <token>` header
- Provider sync (Garmin/Strava/Fitbit) uses OAuth — stubs in v1

## Running Locally

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Tests
cd backend && pytest
cd frontend && npm test
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/steps_challenge` |
| `JWT_SECRET` | Secret key for JWT signing | `CHANGE-ME-in-production` |
| `JWT_EXPIRE_MINUTES` | Token expiry | `1440` (24h) |
| `MILES_CLUB_GOLD` | Gold tier threshold (steps/month) | `300000` |
| `MILES_CLUB_SILVER` | Silver tier threshold | `200000` |
| `MILES_CLUB_BRONZE` | Bronze tier threshold | `100000` |
| `STEPS_PER_MILE` | Steps-to-miles conversion | `2000` |

## Common Tasks

### Add a new API endpoint
1. Create/update Pydantic schema in `backend/app/schemas/`
2. Add business logic in `backend/app/services/`
3. Create route in `backend/app/routers/`
4. Include router in `backend/app/main.py`
5. Write tests in `backend/tests/`

### Add a new frontend page
1. Create page module in `frontend/src/pages/`
2. Add route in `frontend/src/router.ts`
3. Import styles from `frontend/src/styles/`
4. Write tests in `frontend/tests/`

### Add a database migration
```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```
