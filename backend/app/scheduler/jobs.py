"""APScheduler job registry.

All long-running scheduled tasks live here. The runner wires them onto an
``AsyncIOScheduler`` instance.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.models.enums import LessonStatus, ReviewStatus
from app.models.goal import Goal
from app.models.lesson import Lesson
from app.models.notification import Notification
from app.models.review import Review
from app.models.user import User
from app.services.lesson_service import LessonService


log = get_logger(__name__)


INTERVALS_DAYS = [1, 3, 7, 14, 30]


async def job_generate_daily_lessons() -> None:
    """For every active goal, generate today's lessons if not already present."""
    db = SessionLocal()
    try:
        svc = LessonService(db)
        n = await svc.generate_today_for_all_users(target_date=date.today())
        log.info("job_generate_daily_lessons produced %d lessons", n)
    finally:
        db.close()


async def job_schedule_reviews_for_completed_lessons() -> None:
    """Find lessons completed since the last run that don't have reviews yet,
    and create the 1d/3d/7d/14d/30d chain."""
    db = SessionLocal()
    try:
        # Lessons completed in the last 30 minutes that have zero reviews.
        cutoff = datetime.now(timezone.utc).replace(microsecond=0)
        since = cutoff - __import__("datetime").timedelta(minutes=30)
        stmt = (
            select(Lesson)
            .where(Lesson.status == LessonStatus.done)
            .where(Lesson.completed_at >= since)
        )
        lessons = list(db.scalars(stmt))
        from app.services.review_service import ReviewService

        for lesson in lessons:
            existing = db.scalars(
                select(Review).where(Review.lesson_id == lesson.id).limit(1)
            ).first()
            if existing:
                continue
            svc = ReviewService(db)
            await svc.schedule_repetition_chain(str(lesson.id))
        log.info("job_schedule_reviews_for_completed_lessons processed %d lessons", len(lessons))
    finally:
        db.close()


async def job_send_lesson_reminders() -> None:
    """Send a Telegram reminder to each user with pending lessons today."""
    db = SessionLocal()
    try:
        today = date.today()
        stmt = (
            select(Goal, User)
            .join(User, User.id == Goal.user_id)
            .where(Goal.status == "active")
        )
        rows = db.execute(stmt).all()
        from app.notifications.telegram_channel import TelegramChannel

        channel = TelegramChannel()
        for goal, user in rows:
            pending = db.scalars(
                select(Lesson).where(
                    Lesson.goal_id == goal.id,
                    Lesson.scheduled_for == today,
                    Lesson.status == LessonStatus.pending,
                )
            ).all()
            if not pending:
                continue
            text = f"📚 Today's plan for '{goal.title}':\n" + "\n".join(
                f"• {l.title} ({l.duration_minutes}m)" for l in pending
            )
            await channel.send(user, payload={"text": text, "kind": "lesson_reminder"})
        log.info("job_send_lesson_reminders done")
    finally:
        db.close()


async def job_send_review_reminders() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        soon = now + timedelta(hours=2)
        stmt = select(Review, User).join(User, User.id == Review.user_id).where(
            Review.status == ReviewStatus.pending,
            Review.scheduled_for <= soon,
        )
        rows = db.execute(stmt).all()
        from app.notifications.telegram_channel import TelegramChannel

        channel = TelegramChannel()
        for review, user in rows:
            text = (
                f"🔁 Review due: lesson from {review.scheduled_for:%Y-%m-%d %H:%M}\n"
                f"Open the dashboard to keep your streak going."
            )
            await channel.send(user, payload={"text": text, "kind": "review_reminder"})
        log.info("job_send_review_reminders sent %d", len(rows))
    finally:
        db.close()


async def job_adaptive_pacing() -> None:
    from app.services.adaptive_service import AdaptiveService

    db = SessionLocal()
    try:
        svc = AdaptiveService(db)
        await svc.evaluate_all_goals()
        log.info("job_adaptive_pacing done")
    finally:
        db.close()


def _cron(hour: int, minute: int = 0) -> CronTrigger:
    return CronTrigger(hour=hour, minute=minute)


def register(scheduler) -> None:
    scheduler.add_job(_run_async(job_generate_daily_lessons), _cron(6, 0), id="generate_daily_lessons")
    scheduler.add_job(
        _run_async(job_schedule_reviews_for_completed_lessons),
        "interval",
        minutes=15,
        id="schedule_reviews",
    )
    scheduler.add_job(_run_async(job_send_lesson_reminders), _cron(8, 0), id="send_lesson_reminders")
    scheduler.add_job(_run_async(job_send_review_reminders), _cron(9, 0), id="send_review_reminders_morning")
    scheduler.add_job(_run_async(job_send_review_reminders), _cron(19, 0), id="send_review_reminders_evening")
    scheduler.add_job(_run_async(job_adaptive_pacing), _cron(23, 30), id="adaptive_pacing")


def _run_async(coro):
    """Wrap a coroutine function so APScheduler can call it as a sync function."""

    def _wrapper():
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        if loop.is_running():
            # Schedule on the running loop and wait for completion.
            return asyncio.run_coroutine_threadsafe(coro(), loop)
        return loop.run_until_complete(coro())

    return _wrapper