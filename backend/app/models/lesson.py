"""Lesson model — a scheduled daily study item."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import LessonStatus
from app.models.mixins import TimestampMixin, UUIDPK


class Lesson(Base, UUIDPK, TimestampMixin):
    __tablename__ = "lessons"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_for: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus, name="lesson_status"),
        nullable=False,
        default=LessonStatus.pending,
        server_default=LessonStatus.pending.value,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_resource_ids: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    goal = relationship("Goal", back_populates="lessons")
    reviews = relationship("Review", back_populates="lesson", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")