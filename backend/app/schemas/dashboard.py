"""Dashboard aggregate schema."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class GoalProgressItem(BaseModel):
    id: uuid.UUID
    title: str
    progress_pct: float
    due_today: int
    due_reviews: int
    status: str


class DashboardOut(BaseModel):
    current_streak_days: int
    completion_pct_30d: float
    lessons_completed_total: int
    study_hours_30d: float
    quiz_average_pct: float
    goals: list[GoalProgressItem] = []
    last_updated: Optional[str] = None