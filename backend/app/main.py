"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import auth as auth_router
from app.routers import steps as steps_router
from app.routers import challenges as challenges_router
from app.routers import leaderboard as leaderboard_router
from app.routers.auth import limiter

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for group step challenges with leaderboards, miles clubs, and trail maps.",
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(auth_router.router)
app.include_router(steps_router.router)
app.include_router(challenges_router.router)
app.include_router(leaderboard_router.router)


@app.get("/health")
def health_check():
    """Smoke test endpoint — returns 200 if the server is running."""
    return {"status": "ok", "app": settings.app_name}
