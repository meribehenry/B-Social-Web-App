from django.core.exceptions import ImproperlyConfigured
from core.logger.logger_client import get_logger
from ..clients.redis_client import get_redis_client
from redis.exceptions import RedisError
from .lua_script import TOKEN_BUCKET_LUA
import time


logger = get_logger(__name__)


class RateLimiterUnavailable(Exception):
    """Raised when Redis cannot be reached."""

def check_token_bucket(
        bucket_name: str,
        capacity: int,
        refill_rate: float,
        requested: int = 1,
    ) -> tuple:
    """
    Return True if the request is allowed.
    Return False if the request is rate limited.
    """

    if capacity <= 0:
        raise ImproperlyConfigured(
            "Token bucket capacity must be greater than zero."
        )

    if refill_rate <= 0:
        raise ImproperlyConfigured(
            "Token bucket refill rate must be greater than zero."
        )

    if requested <= 0:
        raise ImproperlyConfigured(
            "Requested tokens must be greater than zero."
        )


    try:
        redis_client = get_redis_client()

        now = time.time()
        from .lua_script import TOKEN_BUCKET_LUA
        result = redis_client.eval(
            TOKEN_BUCKET_LUA,
            1,
            bucket_name,
            capacity,
            refill_rate,
            now,
            requested,
        )


        allowed = int(result[0])
        remaining = float(result[1])

        if allowed == 1:
            return True, None

        wait_time_in_secs = (requested - remaining)/ refill_rate
        return False, wait_time_in_secs

    except RedisError as exc:
        logger.error(f"Redis Error {exc}")
        raise RateLimiterUnavailable from exc
