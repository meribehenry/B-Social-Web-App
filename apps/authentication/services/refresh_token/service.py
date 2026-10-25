from datetime import datetime, timezone
from core.clients.redis_client import get_app_redis_client
# from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from core.logger.logger_client import get_logger


logger = get_logger(__name__)


def get_refresh_revocation_key(jti: str) -> str:
    return f"revoked_refresh:{jti}"     # Help build the redis key


def revoke_refresh_token(token_string: str):
    logger.info(" Refresh token revocation starting....")

    app_cache = get_app_redis_client()

    token = RefreshToken(token_string)  # Validating the refresh token

    jti = token["jti"]

    # SimpleJWT's official blacklist system.
    token.blacklist()
    logger.info("Refresh token revoked")

    # Calculate remaining lifetime of the refresh token in seconds.
    expires_at = datetime.fromtimestamp(
        token["exp"],
        tz=timezone.utc,
    )

    remaining_seconds = max(
        int(
            (
                expires_at - datetime.now(timezone.utc)
            ).total_seconds()
        ),
        1,
    )

    # Adding the refresh token jti to redis for fast lookup.
    app_cache.set(
        get_refresh_revocation_key(jti),
        1,
        ex=remaining_seconds, # Time to live 
    )
    logger.info("Revoked Refresh token jti added to redis for fast look up")


def is_refresh_token_revoked(jti: str) -> bool:
    logger.info("Checking if refresh token is revoked")

    app_cache = get_app_redis_client()

    key = get_refresh_revocation_key(jti)

    try:
        cached_value = app_cache.get(key)   # Getting the value of the refresh token jti from redis. True if it exist None if not
        logger.info("Checking redis to see if refresh jti is revoked")

    except Exception:
        # Redis failure → We check SimpleJWT database.
        logger.info("Checking DB to see if refresh jti is revoked. Because redis not available")
        return BlacklistedToken.objects.filter(
            token__jti=jti
        ).exists()

    if cached_value is not None:  # Evaluates what redis gave us
        return True

    # Redis miss → authoritative DB check.
    logger.info("Checking DB to see if refresh jti is revoked. Because redis does not have it")
    revoked = BlacklistedToken.objects.filter(
        token__jti=jti
    ).exists()

    if revoked:
        # Adding the refresh jti to redis if it found in the DB
        logger.info("Adding the refresh jti to redis")

        try:
            outstanding = OutstandingToken.objects.get(jti=jti)  # Getting more information on the token

            remaining_seconds = max(
                int(
                    (
                        outstanding.expires_at - datetime.now(timezone.utc)
                    ).total_seconds()
                ),
                1,
            )

            app_cache.set(
                key,
                1,
                ex=remaining_seconds,
            )
            logger.info("Refresh jti added to redis")

        except Exception:
            # DB already contains the authoritative state.
            pass

    return revoked