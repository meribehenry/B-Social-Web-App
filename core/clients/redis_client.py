import redis
from django.conf import settings
 
# _pool = redis.ConnectionPool.from_url(settings.base.REDIS_URL)
 
# def get_redis_client() -> redis.Redis:
#     """Shared connection pool — call this, never redis.Redis() directly."""
#     return redis.Redis(connection_pool=_pool)

_pool = None
 
def get_redis_client() -> redis.Redis:

    """Shared connection pool — call this, never redis.Redis() directly."""

    global _pool
    if _pool is None:
        redis_url = getattr(settings, "REDIS_URL")
        if redis_url is None:
            redis_url = "redis://127.0.0.1:6379/0"

        _pool = redis.ConnectionPool.from_url(redis_url)

    return redis.Redis(connection_pool=_pool)
