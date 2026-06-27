"""User model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPK


class User(Base, UUIDPK, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    telegram_link_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    telegram_link_code_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="user", cascade="all, delete-orphan")