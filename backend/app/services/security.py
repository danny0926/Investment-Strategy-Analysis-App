"""Security utilities for hashing and JWT."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import settings
from app.schemas.auth import TokenPayload


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def create_access_token(subject: int, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.security.access_token_expire_minutes)
    )
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": settings.security.jwt_issuer,
        "aud": settings.security.jwt_audience,
    }
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)


def create_refresh_token(subject: int) -> str:
    """Create refresh token."""

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.security.refresh_token_expire_minutes
    )
    payload = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "iss": settings.security.jwt_issuer,
        "aud": settings.security.jwt_audience,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.security.secret_key, algorithm=settings.security.algorithm)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""

    return pwd_context.hash(password)


def decode_token(token: str) -> TokenPayload:
    """Decode JWT token and return payload."""

    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
            audience=settings.security.jwt_audience,
            issuer=settings.security.jwt_issuer,
        )
    except JWTError as exc:  # pragma: no cover - defensive branch
        raise ValueError("Invalid token") from exc
    return TokenPayload(
        sub=int(payload["sub"]),
        exp=int(payload["exp"]),
        iat=int(payload["iat"]),
        iss=str(payload["iss"]),
        aud=str(payload["aud"]),
    )
