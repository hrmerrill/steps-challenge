"""Auth router — registration, login, current-user endpoint, profile photo upload, and password reset."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import (
    create_access_token,
    create_password_reset_token,
    get_current_user,
    hash_password,
    reset_password,
    validate_reset_token,
    verify_password,
)
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

PHOTO_SUBDIR = "profile_photos"
_ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _photo_dir() -> str:
    """Return absolute path to the profile photos directory, creating it if needed."""
    path = os.path.join(settings.upload_dir, PHOTO_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def _allowed_content_types() -> set[str]:
    """Return the set of MIME types accepted for profile photo uploads."""
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
    return _user_response(current_user)


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

    # Delete old photo if it exists and is inside the upload directory
    _remove_old_photo(current_user.profile_photo_url)

    ext = os.path.splitext(file.filename or "photo.jpg")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(_photo_dir(), filename)

    with open(dest, "wb") as f:
        f.write(contents)

    url = f"/{settings.upload_dir}/{PHOTO_SUBDIR}/{filename}"
    current_user.profile_photo_url = url
    db.commit()
    db.refresh(current_user)

    return _user_response(current_user)


@router.delete("/profile-photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove the user's profile photo."""
    if current_user.profile_photo_url:
        _remove_old_photo(current_user.profile_photo_url)
        current_user.profile_photo_url = None
        db.commit()


def _remove_old_photo(url: str | None) -> None:
    """Delete a previously uploaded photo, guarding against path traversal.

    Only removes files that resolve to a path inside ``settings.upload_dir``.
    """
    if not url:
        return
    relative = url.lstrip("/")
    target = Path(relative).resolve()
    upload_root = Path(settings.upload_dir).resolve()
    try:
        target.relative_to(upload_root)
    except ValueError:
        return  # path outside upload dir — refuse to delete
    if target.is_file():
        target.unlink()


def _user_response(user: User) -> UserResponse:
    """Build a UserResponse from a User ORM instance."""
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        profile_photo_url=user.profile_photo_url,
        preferred_step_source=user.preferred_step_source,
        garmin_connected=user.garmin_token is not None,
        strava_connected=user.strava_token is not None,
        google_health_connected=user.google_health_token is not None,
    )


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def forgot_password(body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Request a password reset email.

    Always returns a success message to prevent email enumeration.
    """
    _message = "If an account exists with that email, you will receive a password reset link."

    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return MessageResponse(message=_message)

    token = create_password_reset_token(db, user.id)
    await send_password_reset_email(body.email, token)

    return MessageResponse(message=_message)


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def do_reset_password(body: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Reset a user's password using a valid reset token."""
    token_record = validate_reset_token(db, body.token)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or has expired",
        )

    new_hash = hash_password(body.new_password)
    reset_password(db, token_record, new_hash)

    return MessageResponse(message="Password reset successfully")
