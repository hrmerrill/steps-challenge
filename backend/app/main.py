"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth as auth_router
from app.routers import steps as steps_router
from app.routers import challenges as challenges_router
from app.routers import leaderboard as leaderboard_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for group step challenges with leaderboards, miles clubs, and trail maps.",
)

# CORS — allow local dev frontend and configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router)
app.include_router(steps_router.router)
app.include_router(challenges_router.router)
app.include_router(leaderboard_router.router)


@app.get("/health")
def health_check():
    """Smoke test endpoint — returns 200 if the server is running."""
    return {"status": "ok", "app": settings.app_name}
