"""Quiz + QuizAttempt models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import QuizKind
from app.models.mixins import TimestampMixin, UUIDPK


class Quiz(Base, UUIDPK, TimestampMixin):
    __tablename__ = "quizzes"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[QuizKind] = mapped_column(
        Enum(QuizKind, name="quiz_kind"),
        nullable=False,
        default=QuizKind.mixed,
        server_default=QuizKind.mixed.value,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    questions: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    goal = relationship("Goal", back_populates="quizzes")
    lesson = relationship("Lesson", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base, UUIDPK, TimestampMixin):
    __tablename__ = "quiz_attempts"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    feedback: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    quiz = relationship("Quiz", back_populates="attempts")