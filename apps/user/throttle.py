from core.rate_limiting.throttle import GlobalTokenBucketThrottle

class EditProfileTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 10
    refill_rate = 1/3600
    redis_unavailable_value = False
    bucket_name_suffix = "edit-profile"