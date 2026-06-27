"""Redis client (single shared connection pool)."""
from __future__ import annotations

import redis

from app.core.config import settings


redis_client: redis.Redis = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    health_check_interval=30,
)


def get_redis() -> redis.Redis:
    return redis_client