"""Goal model — a learning objective with a daily-time budget."""
from __future__ import annotations

import uuid

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import GoalStatus
from app.models.mixins import TimestampMixin, UUIDPK


class Goal(Base, UUIDPK, TimestampMixin):
    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus, name="goal_status"),
        nullable=False,
        default=GoalStatus.active,
        server_default=GoalStatus.active.value,
    )
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")

    user = relationship("User", back_populates="goals")
    resources = relationship("Resource", back_populates="goal", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="goal", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="goal", cascade="all, delete-orphan")