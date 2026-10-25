import os

import redis
from django.conf import settings
 
# _pool = redis.ConnectionPool.from_url(settings.base.REDIS_URL)
 
# def get_redis_client() -> redis.Redis:
#     """Shared connection pool — call this, never redis.Redis() directly."""
#     return redis.Redis(connection_pool=_pool)

_pool = None
 
def get_redis_client(redis_url=None) -> redis.Redis:

    """Shared connection pool — call this, never redis.Redis() directly."""

    global _pool
    if _pool is None:
        # redis_url = getattr(settings, "REDIS_URL")
        if redis_url is None:
            redis_url = "redis://127.0.0.1:6379/0"

        _pool = redis.ConnectionPool.from_url(redis_url)

    return redis.Redis(connection_pool=_pool)


def get_rate_limit_redis_client() -> redis.Redis:
    """This is for rate limiting"""
    return get_redis_client(redis_url=settings.REDIS_RATE_LIMIT_URL)


def get_app_redis_client() -> redis.Redis:
    """This is for application cache"""
    return get_redis_client(redis_url=settings.REDIS_APP_URL)


def get_analytics_redis_client() -> redis.Redis:
    """This is for analytics"""
    return get_redis_client(redis_url=settings.REDIS_ANALYTICS_URL)
