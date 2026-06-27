"""RQ task definitions.

These are the jobs enqueued from the API and the scheduler. They open their
own DB session because they run in a worker process, not the FastAPI app.
"""
from __future__ import annotations

import asyncio

from rq import Queue

from app.core.logging import get_logger
from app.database.redis import get_redis


log = get_logger(__name__)


def get_queue(name: str = "default") -> Queue:
    return Queue(name, connection=get_redis())


def enqueue_resource_enrichment(resource_id: str) -> None:
    """Enqueue an enrichment job for a resource."""
    try:
        get_queue().enqueue(run_resource_enrichment, resource_id)
    except Exception as exc:
        log.warning("redis unavailable, skipping enqueue: %s", exc)
        # Fall back to inline execution so the user still sees results
        run_resource_enrichment(resource_id)


def enqueue_review_generation(lesson_id: str) -> None:
    try:
        get_queue().enqueue(run_review_generation, lesson_id)
    except Exception as exc:
        log.warning("redis unavailable for review enqueue: %s", exc)
        run_review_generation(lesson_id)


def enqueue_quiz_evaluation(quiz_id: str, attempt_id: str) -> None:
    try:
        get_queue().enqueue(run_quiz_evaluation, quiz_id, attempt_id)
    except Exception as exc:
        log.warning("redis unavailable for quiz eval enqueue: %s", exc)
        run_quiz_evaluation(quiz_id, attempt_id)


# ----- sync wrappers around async code -----


def run_resource_enrichment(resource_id: str) -> None:
    from app.database.session import SessionLocal
    from app.services.resource_service import ResourceService

    async def _go():
        db = SessionLocal()
        try:
            svc = ResourceService(db)
            await svc.enrich(resource_id)
        finally:
            db.close()

    asyncio.run(_go())


def run_review_generation(lesson_id: str) -> None:
    from app.database.session import SessionLocal
    from app.services.review_service import ReviewService

    async def _go():
        db = SessionLocal()
        try:
            svc = ReviewService(db)
            await svc.schedule_repetition_chain(lesson_id)
        finally:
            db.close()

    asyncio.run(_go())


def run_quiz_evaluation(quiz_id: str, attempt_id: str) -> None:
    # Currently the attempt is evaluated synchronously inside the API call
    # because it's user-facing latency. This worker is reserved for future
    # asynchronous deep evaluations.
    log.info("quiz eval task queued (currently no-op): quiz=%s attempt=%s", quiz_id, attempt_id)


__all__ = [
    "enqueue_resource_enrichment",
    "enqueue_review_generation",
    "enqueue_quiz_evaluation",
    "run_resource_enrichment",
    "run_review_generation",
]