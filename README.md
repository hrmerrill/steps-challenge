# 🚶 Steps Challenge

A webapp for group step challenges with leaderboards, miles clubs, and a virtual trail map.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | TypeScript · Vite · Leaflet.js · CSS (custom properties) |
| **Backend** | Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Alembic |
| **Database** | PostgreSQL (SQLite for local dev/testing) |
| **Testing** | pytest (backend) · Vitest (frontend) |
| **CI** | GitHub Actions — runs both test suites on push/PR |

## Features

- **Monthly step challenges** — compete with coworkers
- **Fitness tracker sync** — Garmin, Strava, Google Health API (OAuth) or manual daily entry
- **Miles Clubs** — tiers based on average daily steps from prior month (0–5k, 5k–10k, >10k steps/day)
- **Leaderboard** — ranked by total steps, with miles club badges
- **Virtual Trail Map** — collective progress along the Appalachian Trail (Leaflet.js)
- **Card-based UI** — modern, responsive, sleek design

## Architecture

```
steps-challenge/
├── backend/            Python API (FastAPI)
│   ├── app/
│   │   ├── main.py         Entry point + health check
│   │   ├── config.py       Environment settings
│   │   ├── database.py     SQLAlchemy engine + sessions
│   │   ├── models/         ORM models
│   │   ├── routers/        API route handlers
│   │   ├── services/       Business logic
│   │   └── schemas/        Pydantic request/response models
│   ├── tests/              Unit tests (pytest)
│   └── alembic/            Database migrations
├── frontend/           TypeScript SPA (Vite)
│   ├── src/
│   │   ├── main.ts         App entry
│   │   ├── api.ts          API client (JWT auth)
│   │   ├── pages/          Page modules
│   │   ├── components/     Reusable UI components
│   │   └── styles/         CSS design system
│   └── tests/              Unit tests (Vitest)
└── .github/
    ├── copilot-instructions.md   Developer guide for AI assistants
    └── workflows/ci.yml          CI pipeline
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (optional — SQLite works for local dev)

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with SQLite for local development
DATABASE_URL=sqlite:///./dev.db uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api to backend)
npm run dev
```

The app will be available at `http://localhost:5173`.

### Running Tests

```bash
# Backend tests (uses in-memory SQLite — no DB setup needed)
cd backend
source .venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test
```

### Local Smoke Test

After starting both servers:

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok","app":"Steps Challenge"}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/steps_challenge` |
| `JWT_SECRET` | Secret for signing JWT tokens (**required**, 32+ chars) | — |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes | `1440` (24 hours) |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173,http://localhost:3000` |
| `MILES_CLUB_HIGH` | High tier threshold (avg steps/day) | `10000` |
| `MILES_CLUB_MID` | Mid tier threshold (avg steps/day) | `5000` |
| `UPLOAD_DIR` | Directory for user-uploaded files | `uploads` |
| `MAX_PHOTO_SIZE` | Max profile photo size in bytes | `5242880` (5 MB) |

Copy `.env.example` to `.env` and fill in real values before running.

## Database Migrations

```bash
cd backend
source .venv/bin/activate

# Create a new migration after changing models
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head
```

## Production Deployment

### Quick start with Docker Compose

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET and POSTGRES_PASSWORD

# 2. Generate a strong JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Paste the output into .env as JWT_SECRET

# 3. Build and start
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head
```

The app will be available at `http://localhost:8080` (or `FRONTEND_PORT`).

### Manual deployment (no Docker)

1. **Database** — provision a PostgreSQL 15+ instance and set `DATABASE_URL`.
2. **Backend** — install Python 3.11+, create a venv, `pip install -r requirements.txt`,
   run `alembic upgrade head`, then start with
   `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`.
3. **Frontend** — `npm ci && npm run build`, then serve the `dist/` directory with
   Nginx, Caddy, or any static file server. Proxy `/api` requests to the backend.

### Production checklist

- [ ] `JWT_SECRET` is a strong random string (32+ chars)
- [ ] `POSTGRES_PASSWORD` is unique and strong
- [ ] `CORS_ORIGINS` is set to your production domain only
- [ ] HTTPS is terminated at the reverse proxy (Nginx/Caddy/ALB)
- [ ] Database backups are configured (pg_dump cron or managed service)
- [ ] `DEBUG=false` (default)
- [ ] Upload volume is backed up or stored on durable storage (S3, etc.)

## Contributing

See [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for coding conventions, patterns, and common tasks.

## License

See [LICENSE](LICENSE) for details.
