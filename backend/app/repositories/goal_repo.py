"""Goal repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import GoalStatus
from app.models.goal import Goal


class GoalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, goal_id: uuid.UUID) -> Goal | None:
        return self.db.get(Goal, goal_id)

    def list_for_user(
        self, user_id: uuid.UUID, *, status: GoalStatus | None = None
    ) -> list[Goal]:
        stmt = select(Goal).where(Goal.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Goal.status == status)
        stmt = stmt.order_by(Goal.created_at.desc())
        return list(self.db.scalars(stmt))

    def add(self, goal: Goal) -> Goal:
        self.db.add(goal)
        self.db.flush()
        return goal

    def commit(self) -> None:
        self.db.commit()