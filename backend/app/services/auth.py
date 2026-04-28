"""Auth service — password hashing, JWT creation/verification, current-user dependency."""

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User

security = HTTPBearer()

_RESET_TOKEN_EXPIRY_HOURS = 1


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check *plain* text password against a bcrypt *hashed* value."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    """Create a signed JWT containing the *user_id* as the ``sub`` claim."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> int:
    """Decode JWT and return user_id. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
        return user_id
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency — extracts and validates the JWT, returns the User."""
    user_id = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def create_password_reset_token(db: Session, user_id: int) -> str:
    """Generate a secure reset token, store it, and return the token string."""
    token_str = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_RESET_TOKEN_EXPIRY_HOURS)

    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token_str,
        expires_at=expires_at,
    )
    db.add(reset_token)
    db.commit()
    return token_str


def validate_reset_token(db: Session, token: str) -> PasswordResetToken | None:
    """Look up a reset token. Returns None if invalid, used, or expired."""
    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    return record


def reset_password(db: Session, token_record: PasswordResetToken, new_password_hash: str) -> None:
    """Update the user's password and mark the token as used."""
    user = db.query(User).filter(User.id == token_record.user_id).first()
    if user:
        user.password_hash = new_password_hash
    token_record.used = True
    db.commit()
