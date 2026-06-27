"""User repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get_by_telegram_chat_id(self, chat_id: str) -> User | None:
        return self.db.scalar(select(User).where(User.telegram_chat_id == str(chat_id)))

    def get_by_telegram_link_code(self, code: str) -> User | None:
        return self.db.scalar(select(User).where(User.telegram_link_code == code))

    def list_all(self) -> list[User]:
        return list(self.db.scalars(select(User)))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def commit(self) -> None:
        self.db.commit()

    def delete(self, user: User) -> None:
        self.db.delete(user)