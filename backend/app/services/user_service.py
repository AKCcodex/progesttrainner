"""User service — profile + Telegram linking."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserUpdateIn


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def update_profile(self, user: User, payload: UserUpdateIn) -> User:
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.timezone is not None:
            user.timezone = payload.timezone
        self.db.commit()
        self.db.refresh(user)
        return user

    def issue_telegram_link_code(self, user: User) -> tuple[str, datetime]:
        code = secrets.token_hex(3).upper()  # 6 hex chars — short enough for Telegram
        user.telegram_link_code = code
        user.telegram_link_code_expires_at = _utcnow() + timedelta(minutes=5)
        self.db.commit()
        return code, user.telegram_link_code_expires_at

    def link_telegram_chat(self, code: str, chat_id: str) -> User:
        user = self.repo.get_by_telegram_link_code(code)
        if user is None:
            raise ValueError("invalid link code")
        if (
            user.telegram_link_code_expires_at is None
            or user.telegram_link_code_expires_at < _utcnow()
        ):
            raise ValueError("link code expired")
        # If the chat_id is already associated with another user, detach it first.
        existing = self.repo.get_by_telegram_chat_id(chat_id)
        if existing and existing.id != user.id:
            existing.telegram_chat_id = None
        user.telegram_chat_id = str(chat_id)
        user.telegram_link_code = None
        user.telegram_link_code_expires_at = None
        self.db.commit()
        self.db.refresh(user)
        return user