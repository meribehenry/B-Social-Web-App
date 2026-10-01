from core.rate_limiting.throttle import GlobalTokenBucketThrottle

class LoginTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 5
    refill_rate = 1/120
    redis_unavailable_value = False
    bucket_name_suffix = "login"


class RegisterTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 5
    refill_rate = 1/30
    redis_unavailable_value = False
    bucket_name_suffix = "register"


class OTPVerificationTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 3
    refill_rate = 1/15
    redis_unavailable_value = False
    bucket_name_suffix = "otp-verification"


class ResendOTPTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 5
    refill_rate = 1/60
    redis_unavailable_value = False
    bucket_name_suffix = "resend-otp"


class RefreshTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 10
    refill_rate = 1/10
    redis_unavailable_value = False
    bucket_name_suffix = 'refresh'


class PasswordResetRequestTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 5
    refill_rate = 1/90
    redis_unavailable_value = False
    bucket_name_suffix = 'password-reset-request'

class PasswordResetTokenBucketThrottle(GlobalTokenBucketThrottle):
    capacity = 10
    refill_rate = 1/60
    redis_unavailable_value = False
    bucket_name_suffix = 'password-reset'
    