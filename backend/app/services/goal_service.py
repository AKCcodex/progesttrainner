"""Goal service."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.enums import GoalStatus
from app.models.goal import Goal
from app.repositories.goal_repo import GoalRepository


class GoalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GoalRepository(db)

    def create(self, user_id: uuid.UUID, *, title: str, description: str | None,
               daily_minutes: int, target_date=None) -> Goal:
        goal = Goal(
            user_id=user_id,
            title=title,
            description=description,
            daily_minutes=daily_minutes,
            target_date=target_date,
            status=GoalStatus.active,
        )
        self.repo.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def list_for_user(self, user_id: uuid.UUID, *, status: GoalStatus | None = None) -> list[Goal]:
        return self.repo.list_for_user(user_id, status=status)

    def get(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
        goal = self.repo.get(goal_id)
        if goal is None or goal.user_id != user_id:
            raise LookupError("goal not found")
        return goal

    def update(self, user_id: uuid.UUID, goal_id: uuid.UUID, **fields) -> Goal:
        goal = self.get(user_id, goal_id)
        for key, value in fields.items():
            if value is not None and hasattr(goal, key):
                setattr(goal, key, value)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def soft_delete(self, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
        goal = self.get(user_id, goal_id)
        goal.status = GoalStatus.archived
        self.db.commit()