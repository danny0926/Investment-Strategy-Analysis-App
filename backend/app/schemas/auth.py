"""Authentication schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    """JWT access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")


class TokenPayload(BaseModel):
    """Payload stored within JWT tokens."""

    sub: int
    exp: int
    iat: int
    iss: str
    aud: str


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    password: str
    country: str | None = None
    tz: str | None = None


class RefreshRequest(BaseModel):
    """Request to refresh access tokens."""

    refresh_token: str


class UserResponse(BaseModel):
    """Return basic user data."""

    id: int
    email: EmailStr
    country: str | None
    tz: str
    created_at: datetime

    class Config:
        orm_mode = True
