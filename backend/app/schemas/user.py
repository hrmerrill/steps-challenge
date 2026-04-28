"""Pydantic schemas for user-related requests and responses."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.steps import StepSource


class UserCreate(BaseModel):
    """Schema for new user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def _password_complexity(cls, v: str) -> str:
        """Require at least one uppercase, one lowercase, one digit, and one symbol."""
        checks = [
            (r"[A-Z]", "one uppercase letter"),
            (r"[a-z]", "one lowercase letter"),
            (r"\d", "one digit"),
            (r"[^A-Za-z0-9]", "one special character"),
        ]
        missing = [msg for pattern, msg in checks if not re.search(pattern, v)]
        if missing:
            raise ValueError(f"Password must contain at least {', '.join(missing)}")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    profile_photo_url: str | None = None
    preferred_step_source: StepSource = StepSource.MANUAL
    garmin_connected: bool = False
    strava_connected: bool = False
    google_health_connected: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting a password with a valid token."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_complexity(cls, v: str) -> str:
        """Require at least one uppercase, one lowercase, one digit, and one symbol."""
        checks = [
            (r"[A-Z]", "one uppercase letter"),
            (r"[a-z]", "one lowercase letter"),
            (r"\d", "one digit"),
            (r"[^A-Za-z0-9]", "one special character"),
        ]
        missing = [msg for pattern, msg in checks if not re.search(pattern, v)]
        if missing:
            raise ValueError(f"Password must contain at least {', '.join(missing)}")
        return v


class MessageResponse(BaseModel):
    """Generic response with a message."""

    message: str
