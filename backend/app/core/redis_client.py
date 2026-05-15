from __future__ import annotations

import os
from functools import lru_cache

from redis import Redis
from redis.exceptions import RedisError


REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1").strip() or "127.0.0.1"
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
REDIS_DECODE_RESPONSES = os.getenv("REDIS_DECODE_RESPONSES", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
REDIS_SOCKET_CONNECT_TIMEOUT = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
REDIS_SOCKET_TIMEOUT = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
REDIS_URL = os.getenv("REDIS_URL", "").strip()


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    if REDIS_URL:
        return Redis.from_url(
            REDIS_URL,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=REDIS_DECODE_RESPONSES,
            socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=REDIS_SOCKET_TIMEOUT,
            health_check_interval=30,
        )

    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=REDIS_DECODE_RESPONSES,
        socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
        socket_timeout=REDIS_SOCKET_TIMEOUT,
        health_check_interval=30,
    )


def ping_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except RedisError:
        return False
