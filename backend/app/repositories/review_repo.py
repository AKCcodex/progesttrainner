"""Review repository."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ReviewStatus
from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, review_id: uuid.UUID) -> Review | None:
        return self.db.get(Review, review_id)

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        status: ReviewStatus | None = None,
    ) -> list[Review]:
        stmt = select(Review).where(Review.user_id == user_id)
        if from_dt is not None:
            stmt = stmt.where(Review.scheduled_for >= from_dt)
        if to_dt is not None:
            stmt = stmt.where(Review.scheduled_for <= to_dt)
        if status is not None:
            stmt = stmt.where(Review.status == status)
        stmt = stmt.order_by(Review.scheduled_for.asc())
        return list(self.db.scalars(stmt))

    def list_for_lesson(self, lesson_id: uuid.UUID) -> list[Review]:
        return list(
            self.db.scalars(
                select(Review).where(Review.lesson_id == lesson_id).order_by(Review.scheduled_for.asc())
            )
        )

    def add(self, review: Review) -> Review:
        self.db.add(review)
        self.db.flush()
        return review

    def add_all(self, reviews: list[Review]) -> list[Review]:
        for r in reviews:
            self.db.add(r)
        self.db.flush()
        return reviews

    def commit(self) -> None:
        self.db.commit()