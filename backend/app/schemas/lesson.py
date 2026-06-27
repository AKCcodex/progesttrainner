"""Lesson + review schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import LessonStatus, ReviewStatus


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    scheduled_for: date
    title: str
    description: Optional[str]
    duration_minutes: int
    status: LessonStatus
    completed_at: Optional[datetime]
    source_resource_ids: list
    order_index: int
    created_at: datetime


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    scheduled_for: datetime
    interval_days: int
    repetition_index: int
    status: ReviewStatus
    completed_at: Optional[datetime]


class LessonCompleteIn(BaseModel):
    """Empty payload — completion is idempotent."""