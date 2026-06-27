"""Quiz schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import QuizKind


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    lesson_id: Optional[uuid.UUID]
    title: Optional[str]
    kind: QuizKind
    questions: list[dict]
    created_at: datetime


class QuizSubmissionIn(BaseModel):
    answers: list[dict] = Field(
        description="List of {question_id, answer} entries.",
    )


class QuizAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quiz_id: uuid.UUID
    score: float
    feedback: dict
    submitted_at: datetime