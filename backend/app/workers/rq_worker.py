"""RQ worker entrypoint.

Run via: ``python -m app.workers.rq_worker``
"""
from __future__ import annotations

from rq import Queue, Worker

from app.core.logging import configure_logging, get_logger
from app.database.redis import get_redis


configure_logging()
log = get_logger(__name__)


def main() -> None:
    connection = get_redis()
    queues = [Queue(name="default", connection=connection)]
    log.info("rq worker starting on queues: %s", [q.name for q in queues])
    worker = Worker(queues, connection=connection)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()