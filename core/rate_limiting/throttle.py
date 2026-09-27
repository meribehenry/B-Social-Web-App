from rest_framework.throttling import BaseThrottle
from .limiter import check_token_bucket, RateLimiterUnavailable



class GlobalTokenBucketThrottle(BaseThrottle):

    capacity = 100

    # 2 requests per second.
    refill_rate = 2.0

    def allow_request(self, request, view):

        if (
            request.user
            and request.user.is_authenticated
        ):
            identity = f"user:{request.user.id}"

        else:
            identity = f"ip:{self.get_ident(request)}"

        bucket_name = f"ratelimit:global:{identity}"
        


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

            # Fail open for the global limiter.
            return True

    def wait(self):
        return self._wait
