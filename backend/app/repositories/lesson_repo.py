"""Lesson repository."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import LessonStatus
from app.models.lesson import Lesson


class LessonRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, lesson_id: uuid.UUID) -> Lesson | None:
        return self.db.get(Lesson, lesson_id)

    def list_for_goal(
        self,
        goal_id: uuid.UUID,
        *,
        on_date: date | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        status: LessonStatus | None = None,
    ) -> list[Lesson]:
        stmt = select(Lesson).where(Lesson.goal_id == goal_id)
        if on_date is not None:
            stmt = stmt.where(Lesson.scheduled_for == on_date)
        if from_date is not None:
            stmt = stmt.where(Lesson.scheduled_for >= from_date)
        if to_date is not None:
            stmt = stmt.where(Lesson.scheduled_for <= to_date)
        if status is not None:
            stmt = stmt.where(Lesson.status == status)
        stmt = stmt.order_by(Lesson.scheduled_for.asc(), Lesson.order_index.asc())
        return list(self.db.scalars(stmt))

    def add(self, lesson: Lesson) -> Lesson:
        self.db.add(lesson)
        self.db.flush()
        return lesson

    def commit(self) -> None:
        self.db.commit()