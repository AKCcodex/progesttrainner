"""Adaptive service — pacing adjustments based on performance."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import GoalStatus, LessonStatus, ReviewStatus
from app.models.goal import Goal
from app.models.lesson import Lesson
from app.models.quiz import QuizAttempt
from app.models.review import Review


log = get_logger(__name__)


class AdaptiveService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def evaluate_all_goals(self) -> int:
        goals = list(self.db.scalars(select(Goal).where(Goal.status == GoalStatus.active)))
        changes = 0
        for goal in goals:
            try:
                if await self.evaluate_goal(goal):
                    changes += 1
            except Exception as exc:
                log.exception("adaptive evaluation failed for goal %s: %s", goal.id, exc)
        self.db.commit()
        log.info("adaptive_pacing: adjusted %d/%d goals", changes, len(goals))
        return changes

    async def evaluate_goal(self, goal: Goal) -> bool:
        """Return True if we modified the goal."""
        now = datetime.now(timezone.utc)
        fourteen_days_ago = now - timedelta(days=14)

        lessons_last_7 = list(
            self.db.scalars(
                select(Lesson).where(
                    Lesson.goal_id == goal.id, Lesson.scheduled_for >= date.today() - timedelta(days=7)
                )
            )
        )
        completed = [lesson for lesson in lessons_last_7 if lesson.status == LessonStatus.done]
        scheduled = len(lessons_last_7) or 1
        completion_rate = len(completed) / scheduled

        attempts = list(
            self.db.scalars(
                select(QuizAttempt).where(
                    QuizAttempt.user_id == goal.user_id,
                    QuizAttempt.submitted_at >= fourteen_days_ago,
                )
            )
        )
        quiz_avg = (sum(a.score for a in attempts) / len(attempts)) if attempts else 0.0

        original_minutes = goal.daily_minutes

        new_minutes = goal.daily_minutes
        skip_long = False

        # Regress: completion is poor → ease off.
        if completion_rate < settings.ADAPTIVE_REDUCE_THRESHOLD:
            new_minutes = max(
                settings.ADAPTIVE_MIN_DAILY_MINUTES,
                int(goal.daily_minutes * 0.8),
            )
            current_meta = dict(goal.meta or {})
            current_meta["adaptive_reason"] = "low_completion"
            goal.meta = current_meta

        # Accelerate: high completion AND high quiz score → push harder.
        elif (
            quiz_avg >= settings.ADAPTIVE_INCREASE_THRESHOLD
            and completion_rate >= settings.ADAPTIVE_COMPLETION_THRESHOLD
        ):
            new_minutes = min(
                settings.ADAPTIVE_MAX_DAILY_MINUTES,
                int(goal.daily_minutes * 1.15),
            )
            skip_long = True
            current_meta = dict(goal.meta or {})
            current_meta["adaptive_reason"] = "high_performance"
            goal.meta = current_meta

        changed = False
        if new_minutes != goal.daily_minutes:
            log.info(
                "adaptive: goal %s daily_minutes %d -> %d (completion=%.2f, quiz_avg=%.2f)",
                goal.id,
                original_minutes,
                new_minutes,
                completion_rate,
                quiz_avg,
            )
            goal.daily_minutes = new_minutes
            changed = True

        # If we accelerated, cancel the 14d/30d review slots for the most recent
        # batch so the learner can move on to new material faster.
        if skip_long:
            recent_reviews = list(
                self.db.scalars(
                    select(Review).where(
                        Review.user_id == goal.user_id,
                        Review.interval_days.in_([14, 30]),
                        Review.scheduled_for > now,
                    )
                )
            )
            for r in recent_reviews:
                r.status = ReviewStatus.done
                r.completed_at = now
            log.info("adaptive: cancelled %d long-interval reviews for goal %s", len(recent_reviews), goal.id)
            changed = changed or bool(recent_reviews)
        return changed


__all__ = ["AdaptiveService"]


# Re-export INTERVALS for the scheduler to use.
__all__.append("INTERVALS_DAYS")  # noqa: WPS410