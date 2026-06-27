"""Goal schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GoalStatus


class GoalCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    daily_minutes: int = Field(default=30, ge=5, le=480)
    target_date: Optional[date] = None


class GoalUpdateIn(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    daily_minutes: Optional[int] = Field(default=None, ge=5, le=480)
    target_date: Optional[date] = None
    status: Optional[GoalStatus] = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: Optional[str]
    daily_minutes: int
    target_date: Optional[date]
    status: GoalStatus
    meta: dict = {}
    created_at: datetime
    updated_at: datetime