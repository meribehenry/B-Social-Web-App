from core.rate_limiting.throttle import GlobalTokenBucketThrottle


class CreateCommentTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 100
    refill_rate = 1/60
    redis_unavailable_value = False
    bucket_name_suffix = "create-comment"


class EditCommentTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 5
    refill_rate = 1/3600
    redis_unavailable_value = False
    bucket_name_suffix = "edit-comment"