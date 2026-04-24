#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Local Development Setup & Launch
#
# Sets up a local dev environment with a seeded SQLite database,
# starts the backend (FastAPI) and frontend (Vite) dev servers.
#
# Usage:
#   ./scripts/local-dev.sh          # full setup + start servers
#   ./scripts/local-dev.sh --seed   # re-seed database only (wipe + reseed)
#   ./scripts/local-dev.sh --stop   # stop running dev servers
#
# After running, the app is available at:
#   Frontend:  http://localhost:5173
#   Backend:   http://localhost:8000
#   API docs:  http://localhost:8000/docs
#
# Test credentials (seeded):
#   alice@example.com / Test1234!   (>10k steps/day tier)
#   bob@example.com   / Test1234!   (>10k steps/day tier)
#   carol@example.com / Test1234!   (5k-10k steps/day tier)
#   dave@example.com  / Test1234!   (5k-10k steps/day tier)
#   eve@example.com   / Test1234!   (0-5k steps/day tier)
#   frank@example.com / Test1234!   (0-5k steps/day tier)
# ---------------------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
PID_DIR="${ROOT_DIR}/.dev-pids"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}▸${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✖${NC} $1" >&2; }

# ---------------------------------------------------------------------------
# Stop running dev servers
# ---------------------------------------------------------------------------
stop_servers() {
    if [ -d "$PID_DIR" ]; then
        for pidfile in "$PID_DIR"/*.pid; do
            [ -f "$pidfile" ] || continue
            pid=$(cat "$pidfile")
            name=$(basename "$pidfile" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                info "Stopped ${name} (PID ${pid})"
            fi
            rm -f "$pidfile"
        done
        rmdir "$PID_DIR" 2>/dev/null || true
    fi
}

if [ "${1:-}" = "--stop" ]; then
    stop_servers
    info "Dev servers stopped."
    exit 0
fi

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
check_command() {
    if ! command -v "$1" &>/dev/null; then
        error "$1 is required but not installed."
        exit 1
    fi
}

check_command python3
check_command node
check_command npm

# ---------------------------------------------------------------------------
# Backend setup
# ---------------------------------------------------------------------------
info "Setting up backend..."

if [ ! -d "${BACKEND_DIR}/.venv" ]; then
    info "Creating Python virtual environment..."
    python3 -m venv "${BACKEND_DIR}/.venv"
fi

source "${BACKEND_DIR}/.venv/bin/activate"

# Install dependencies quietly (only show errors)
pip install -q -r "${BACKEND_DIR}/requirements.txt" 2>&1 | grep -v "already satisfied" || true

# ---------------------------------------------------------------------------
# Frontend setup
# ---------------------------------------------------------------------------
info "Setting up frontend..."

if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
    info "Installing frontend dependencies..."
    (cd "${FRONTEND_DIR}" && npm ci --silent)
else
    info "Frontend dependencies already installed."
fi

# ---------------------------------------------------------------------------
# Database seed
# ---------------------------------------------------------------------------
export DATABASE_URL="sqlite:///${BACKEND_DIR}/dev.db"
export JWT_SECRET="dev-only-secret-not-for-production-use!!"
export CORS_ORIGINS="http://localhost:5173,http://localhost:3000,http://localhost:8080"

if [ "${1:-}" = "--seed" ]; then
    info "Re-seeding database (wiping existing data)..."
    rm -f "${BACKEND_DIR}/dev.db"
    (cd "${BACKEND_DIR}" && python seed_dev.py)
    info "Done! Database re-seeded."
    exit 0
fi

if [ ! -f "${BACKEND_DIR}/dev.db" ]; then
    info "Seeding database with simulated data..."
    (cd "${BACKEND_DIR}" && python seed_dev.py)
else
    info "Database already exists. Use --seed to wipe and re-seed."
fi

# ---------------------------------------------------------------------------
# Stop any previously running servers
# ---------------------------------------------------------------------------
stop_servers

# ---------------------------------------------------------------------------
# Start servers
# ---------------------------------------------------------------------------
mkdir -p "$PID_DIR"

info "Starting backend (FastAPI) on http://localhost:8000 ..."
(cd "${BACKEND_DIR}" && \
    DATABASE_URL="${DATABASE_URL}" \
    JWT_SECRET="${JWT_SECRET}" \
    CORS_ORIGINS="${CORS_ORIGINS}" \
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
    > "${ROOT_DIR}/.dev-backend.log" 2>&1 &
    echo $! > "${PID_DIR}/backend.pid"
)

info "Starting frontend (Vite) on http://localhost:5173 ..."
(cd "${FRONTEND_DIR}" && \
    npm run dev \
    > "${ROOT_DIR}/.dev-frontend.log" 2>&1 &
    echo $! > "${PID_DIR}/frontend.pid"
)

# Wait for backend to be ready
info "Waiting for backend to start..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    info "Backend is ready!"
else
    warn "Backend may still be starting — check .dev-backend.log"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Local dev environment is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${GREEN}http://localhost:5173${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "  Login:     ${YELLOW}alice@example.com${NC} / ${YELLOW}Test1234!${NC}"
echo ""
echo -e "  Logs:      tail -f .dev-backend.log"
echo -e "             tail -f .dev-frontend.log"
echo ""
echo -e "  Stop:      ${YELLOW}./scripts/local-dev.sh --stop${NC}"
echo -e "  Re-seed:   ${YELLOW}./scripts/local-dev.sh --seed${NC}"
echo ""
