"""Lesson service — daily-plan generation + lifecycle."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.ai.provider import get_ai_provider
from app.ai.prompts import (
    SYSTEM_COACH,
    daily_lesson_prompt,
    roadmap_prompt,
)
from app.core.logging import get_logger
from app.models.enums import GoalStatus, LessonStatus, ResourceKind
from app.models.goal import Goal
from app.models.lesson import Lesson
from app.models.resource import Resource
from app.repositories.goal_repo import GoalRepository
from app.repositories.lesson_repo import LessonRepository
from app.repositories.resource_repo import ResourceRepository


log = get_logger(__name__)


def _resources_summary(resources: list[Resource]) -> str:
    parts: list[str] = []
    for r in resources[:20]:
        snippet = (r.content_text or r.transcript or "")[:300]
        meta_bits = []
        if r.meta.get("duration"):
            meta_bits.append(f"duration={r.meta['duration']}")
        if r.meta.get("channel"):
            meta_bits.append(f"channel={r.meta['channel']}")
        meta = f" [{', '.join(meta_bits)}]" if meta_bits else ""
        parts.append(f"- ({r.kind.value}) {r.title}{meta}\n  excerpt: {snippet}")
    return "\n".join(parts) if parts else "(no resources yet)"


def _prior_lessons(lessons: list[Lesson]) -> str:
    if not lessons:
        return ""
    return "\n".join(f"- {l.scheduled_for}: {l.title}" for l in lessons[-10:])


class LessonService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.lesson_repo = LessonRepository(db)
        self.goal_repo = GoalRepository(db)
        self.resource_repo = ResourceRepository(db)

    async def generate_roadmap(self, goal: Goal) -> dict:
        resources = self.resource_repo.list_for_user(goal.user_id, goal_id=goal.id)
        prompt = roadmap_prompt(
            goal.title, goal.description, goal.daily_minutes, _resources_summary(resources)
        )
        provider = get_ai_provider()
        text = await provider.generate(prompt, system=SYSTEM_COACH, temperature=0.4, max_tokens=1200)
        # Roadmap is returned to the caller; persistence of structured roadmap
        # fields would be a follow-up (e.g. a goals.meta JSONB column).
        return {"roadmap_text": text}

    async def generate_daily_lessons(
        self, goal: Goal, target_date: date
    ) -> list[Lesson]:
        """Generate today's lessons for ``goal``. Idempotent: returns existing
        lessons if already generated."""
        existing = self.lesson_repo.list_for_goal(goal.id, on_date=target_date)
        if existing:
            return existing

        resources = self.resource_repo.list_for_user(goal.user_id, goal_id=goal.id)
        prior = self.lesson_repo.list_for_goal(
            goal.id,
            from_date=target_date - timedelta(days=7),
            to_date=target_date - timedelta(days=1),
        )
        prompt = daily_lesson_prompt(
            goal.title,
            goal.daily_minutes,
            _resources_summary(resources),
            target_date.isoformat(),
            _prior_lessons(prior),
        )
        provider = get_ai_provider()
        from app.ai.providers.base import extract_json

        try:
            data = await provider.generate(prompt, system=SYSTEM_COACH, temperature=0.5, max_tokens=1000)
            parsed = extract_json(data)
            plan_items = parsed.get("lessons", []) if isinstance(parsed, dict) else []
        except Exception as exc:
            log.exception("daily lesson generation failed for goal %s: %s", goal.id, exc)
            plan_items = [
                {
                    "title": f"Continue learning: {goal.title}",
                    "description": "Re-read recent resources and summarise key points.",
                    "duration_minutes": min(goal.daily_minutes, 30),
                    "focus_resource_title": "",
                }
            ]

        created: list[Lesson] = []
        for idx, item in enumerate(plan_items):
            if not isinstance(item, dict):
                continue
            lesson = Lesson(
                goal_id=goal.id,
                user_id=goal.user_id,
                scheduled_for=target_date,
                title=item.get("title") or "Untitled lesson",
                description=item.get("description"),
                duration_minutes=int(item.get("duration_minutes") or min(20, goal.daily_minutes)),
                status=LessonStatus.pending,
                source_resource_ids=[],
                order_index=idx,
            )
            self.lesson_repo.add(lesson)
            created.append(lesson)
        self.db.commit()
        for lesson in created:
            self.db.refresh(lesson)
        return created

    def list_for_goal_on_date(
        self, user_id: uuid.UUID, goal_id: uuid.UUID, target_date: date
    ) -> list[Lesson]:
        goal = self.goal_repo.get(goal_id)
        if goal is None or goal.user_id != user_id:
            raise LookupError("goal not found")
        return self.lesson_repo.list_for_goal(goal_id, on_date=target_date)

    def complete(self, user_id: uuid.UUID, lesson_id: uuid.UUID) -> Lesson:
        lesson = self.lesson_repo.get(lesson_id)
        if lesson is None or lesson.user_id != user_id:
            raise LookupError("lesson not found")
        from datetime import datetime, timezone

        lesson.status = LessonStatus.done
        lesson.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(lesson)
        # Schedule spaced-repetition reviews asynchronously.
        from app.workers.tasks import enqueue_review_generation

        try:
            enqueue_review_generation(str(lesson.id))
        except Exception as exc:  # pragma: no cover
            log.warning("could not enqueue review generation: %s", exc)
        return lesson

    def skip(self, user_id: uuid.UUID, lesson_id: uuid.UUID) -> Lesson:
        lesson = self.lesson_repo.get(lesson_id)
        if lesson is None or lesson.user_id != user_id:
            raise LookupError("lesson not found")
        lesson.status = LessonStatus.skipped
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    async def generate_today_for_all_users(self, target_date: date | None = None) -> int:
        """Used by APScheduler. Generates lessons for every active goal across all users."""
        target_date = target_date or date.today()
        # Pull every active goal (cheap query, expected rows < few thousand).
        goals = list(self.db.query(Goal).filter(Goal.status == GoalStatus.active).all())
        count = 0
        for goal in goals:
            try:
                created = await self.generate_daily_lessons(goal, target_date)
                count += len(created)
            except Exception as exc:
                log.exception("lesson generation failed for goal %s: %s", goal.id, exc)
        log.info("generated %d lessons for %d goals on %s", count, len(goals), target_date)
        return count