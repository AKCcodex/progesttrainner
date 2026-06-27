"""APScheduler lifecycle."""
from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger
from app.scheduler.jobs import register as register_jobs


log = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    scheduler = AsyncIOScheduler(timezone="UTC")
    register_jobs(scheduler)
    scheduler.start()
    _scheduler = scheduler
    log.info("scheduler started with %d jobs", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    except Exception as exc:  # pragma: no cover
        log.warning("scheduler shutdown error: %s", exc)
    _scheduler = None


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler