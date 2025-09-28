"""User service functions."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Account, User
from app.schemas.auth import RegisterRequest
from app.services.security import get_password_hash


def create_user(db: Session, data: RegisterRequest) -> User:
    """Create a new user and default account."""

    existing = db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise ValueError("Email already registered")
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        country=data.country,
        tz=data.tz or "Asia/Taipei",
    )
    db.add(user)
    db.flush()
    default_account = Account(
        user_id=user.id,
        account_code=f"{user.id}-SIM",
        currency="TWD",
        nickname="Demo Account",
    )
    db.add(default_account)
    db.commit()
    db.refresh(user)
    return user
