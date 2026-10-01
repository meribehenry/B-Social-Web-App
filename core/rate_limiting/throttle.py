from rest_framework.throttling import BaseThrottle
from .limiter import check_token_bucket, RateLimiterUnavailable
from ..logger.logger_client import get_logger


logger = get_logger(__name__)


class GlobalTokenBucketThrottle(BaseThrottle):

    capacity = 100
    refill_rate = 2.0       # 2 requests per second.
    redis_unavailable_value: bool = True
    bucket_name_suffix = "global"

    def allow_request(self, request, view):

        if (
            request.user
            and request.user.is_authenticated
        ):
            identity = f"user:{request.user.id}"

        else:
            identity = f"ip:{self.get_ident(request)}"

        bucket_name = f"ratelimit:{self.bucket_name_suffix}:{identity}"
        

        try:

            result = check_token_bucket(
                bucket_name=bucket_name,
                capacity=self.capacity,
                refill_rate=self.refill_rate,
                requested=1,
            )

            allowed = result[0]
            self._wait = result[1]


            return allowed

        except RateLimiterUnavailable:
            logger.error("Rate limiter error. Redis unavailable")

            if self.redis_unavailable_value is False:
                logger.info("Service denied for this request")
                
            # Fail open for the global limiter.
            return self.redis_unavailable_value

    def wait(self):
        return self._wait
