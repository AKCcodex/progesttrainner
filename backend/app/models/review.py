"""Review model — spaced repetition entry."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ReviewStatus
from app.models.mixins import TimestampMixin, UUIDPK


class Review(Base, UUIDPK, TimestampMixin):
    __tablename__ = "reviews"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False)
    repetition_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        nullable=False,
        default=ReviewStatus.pending,
        server_default=ReviewStatus.pending.value,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lesson = relationship("Lesson", back_populates="reviews")