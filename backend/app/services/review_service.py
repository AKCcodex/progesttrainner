"""Review service — spaced-repetition chain (1d/3d/7d/14d/30d)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.enums import ReviewStatus
from app.models.review import Review
from app.repositories.review_repo import ReviewRepository


INTERVALS_DAYS = [1, 3, 7, 14, 30]


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReviewRepository(db)

    async def schedule_repetition_chain(self, lesson_id: str) -> list[Review]:
        """Create the standard 1/3/7/14/30-day review chain for a completed lesson."""
        try:
            from app.models.lesson import Lesson

            lesson = self.db.get(Lesson, uuid.UUID(lesson_id))
        except (ValueError, Exception) as exc:
            raise LookupError(f"lesson {lesson_id} not found") from exc
        if lesson is None:
            raise LookupError(f"lesson {lesson_id} not found")

        existing = self.repo.list_for_lesson(lesson.id)
        if existing:
            return existing

        base = lesson.completed_at or datetime.now(timezone.utc)
        reviews = []
        for idx, interval in enumerate(INTERVALS_DAYS):
            r = Review(
                lesson_id=lesson.id,
                user_id=lesson.user_id,
                scheduled_for=base + timedelta(days=interval),
                interval_days=interval,
                repetition_index=idx,
                status=ReviewStatus.pending,
            )
            self.repo.add(r)
            reviews.append(r)
        self.db.commit()
        return reviews

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        status: ReviewStatus | None = None,
    ) -> list[Review]:
        return self.repo.list_for_user(user_id, from_dt=from_dt, to_dt=to_dt, status=status)

    def complete(self, user_id: uuid.UUID, review_id: uuid.UUID) -> Review:
        review = self.repo.get(review_id)
        if review is None or review.user_id != user_id:
            raise LookupError("review not found")
        review.status = ReviewStatus.done
        review.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(review)
        return review