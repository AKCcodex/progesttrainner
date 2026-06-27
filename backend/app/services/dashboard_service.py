"""Dashboard aggregate service."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.enums import GoalStatus, LessonStatus, ReviewStatus
from app.models.goal import Goal
from app.models.lesson import Lesson
from app.models.quiz import QuizAttempt
from app.models.review import Review
from app.schemas.dashboard import DashboardOut, GoalProgressItem


log = get_logger(__name__)


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build(self, user_id: uuid.UUID) -> DashboardOut:
        now = datetime.now(timezone.utc)
        thirty_days_ago = (now - timedelta(days=30)).date()

        # Streak: consecutive days with at least one completed lesson, ending today or yesterday.
        recent_done = list(
            self.db.scalars(
                select(Lesson.completed_at)
                .where(
                    Lesson.user_id == user_id,
                    Lesson.status == LessonStatus.done,
                    Lesson.completed_at.is_not(None),
                )
                .order_by(Lesson.completed_at.desc())
                .limit(200)
            )
        )
        dates = sorted({d.date() for d in recent_done if d}, reverse=True)
        streak = 0
        cursor = date.today()
        if dates and dates[0] == cursor:
            cursor -= timedelta(days=1)
            streak = 1
        elif dates and dates[0] == cursor + timedelta(days=1):
            cursor = dates[0]
        else:
            cursor = None
        if cursor:
            for d in dates:
                if d == cursor:
                    streak += 1
                    cursor -= timedelta(days=1)
                elif d < cursor:
                    break

        # Completion % in last 30 days
        lessons_30d = list(
            self.db.scalars(
                select(Lesson).where(
                    Lesson.user_id == user_id, Lesson.scheduled_for >= thirty_days_ago
                )
            )
        )
        if lessons_30d:
            done = sum(1 for l in lessons_30d if l.status == LessonStatus.done)
            completion_pct = done / len(lessons_30d)
        else:
            completion_pct = 0.0

        lessons_total = self.db.scalar(
            select(func.count(Lesson.id)).where(
                Lesson.user_id == user_id, Lesson.status == LessonStatus.done
            )
        ) or 0

        study_minutes = sum(
            (l.duration_minutes or 0)
            for l in lessons_30d
            if l.status == LessonStatus.done
        )
        study_hours = round(study_minutes / 60.0, 2)

        attempts_30d = list(
            self.db.scalars(
                select(QuizAttempt).where(
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.submitted_at >= now - timedelta(days=30),
                )
            )
        )
        quiz_avg = (sum(a.score for a in attempts_30d) / len(attempts_30d)) if attempts_30d else 0.0

        # Per-goal progress
        goals = list(
            self.db.scalars(
                select(Goal).where(Goal.user_id == user_id, Goal.status != GoalStatus.archived)
            )
        )
        items: list[GoalProgressItem] = []
        for goal in goals:
            lessons = list(
                self.db.scalars(select(Lesson).where(Lesson.goal_id == goal.id))
            )
            if lessons:
                done_n = sum(1 for l in lessons if l.status == LessonStatus.done)
                progress = done_n / len(lessons)
            else:
                progress = 0.0
            due_today = sum(
                1
                for l in lessons
                if l.scheduled_for == date.today() and l.status == LessonStatus.pending
            )
            due_reviews = sum(
                1
                for r in self.db.scalars(
                    select(Review).where(
                        Review.user_id == user_id,
                        Review.status == ReviewStatus.pending,
                        Review.scheduled_for <= now + timedelta(hours=24),
                    )
                )
            )
            items.append(
                GoalProgressItem(
                    id=goal.id,
                    title=goal.title,
                    progress_pct=round(progress, 3),
                    due_today=due_today,
                    due_reviews=due_reviews,
                    status=goal.status.value,
                )
            )

        return DashboardOut(
            current_streak_days=streak,
            completion_pct_30d=round(completion_pct, 3),
            lessons_completed_total=int(lessons_total),
            study_hours_30d=study_hours,
            quiz_average_pct=round(quiz_avg, 3),
            goals=items,
            last_updated=now.isoformat(),
        )