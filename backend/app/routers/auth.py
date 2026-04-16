"""Auth router — registration, login, current-user endpoint, and profile photo upload."""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

PHOTO_SUBDIR = "profile_photos"


def _photo_dir() -> str:
    """Return absolute path to the profile photos directory, creating it if needed."""
    path = os.path.join(settings.upload_dir, PHOTO_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def _allowed_content_types() -> set[str]:
    return {t.strip() for t in settings.allowed_photo_types.split(",") if t.strip()}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(body: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Create a new user account and return a JWT token."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(body: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate and return a JWT token."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        profile_photo_url=current_user.profile_photo_url,
        garmin_connected=current_user.garmin_token is not None,
        strava_connected=current_user.strava_token is not None,
        fitbit_connected=current_user.fitbit_token is not None,
    )


@router.post("/profile-photo", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def upload_profile_photo(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload or replace the user's profile photo."""
    allowed = _allowed_content_types()
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Accepted: {', '.join(sorted(allowed))}",
        )

    contents = await file.read()
    if len(contents) > settings.max_photo_size:
        max_mb = settings.max_photo_size / (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {max_mb:.0f} MB")

    # Delete old photo if exists
    if current_user.profile_photo_url:
        old_path = current_user.profile_photo_url.lstrip("/")
        if os.path.isfile(old_path):
            os.remove(old_path)

    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(_photo_dir(), filename)

    with open(dest, "wb") as f:
        f.write(contents)

    url = f"/{settings.upload_dir}/{PHOTO_SUBDIR}/{filename}"
    current_user.profile_photo_url = url
    db.commit()
    db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        profile_photo_url=current_user.profile_photo_url,
        garmin_connected=current_user.garmin_token is not None,
        strava_connected=current_user.strava_token is not None,
        fitbit_connected=current_user.fitbit_token is not None,
    )


@router.delete("/profile-photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove the user's profile photo."""
    if current_user.profile_photo_url:
        old_path = current_user.profile_photo_url.lstrip("/")
        if os.path.isfile(old_path):
            os.remove(old_path)
        current_user.profile_photo_url = None
        db.commit()
