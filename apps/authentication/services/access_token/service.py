from datetime import datetime, timezone
from django.core.cache import cache
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken
from ...models import RevokedAccessToken
from core.logger.logger_client import get_logger


logger = get_logger(__name__)


def get_access_revocation_key(jti: str) -> str:
    return f"revoked_access:{jti}"  # Help build the redis key


@transaction.atomic
def revoke_access_token_object(token:AccessToken):
    """
    Permanently record the access token as revoked in the DB
    and cache that information in Redis.
    """

    logger.info("Access token revocation starting....")

    jti = token["jti"]
    user_id = token["user_id"]
    exp = token["exp"]

    # Calculate the access token lifetime in seconds
    expires_at = datetime.fromtimestamp(
        exp,
        tz=timezone.utc,
    )

    # PostgreSQL is our source of truth.
    RevokedAccessToken.objects.get_or_create(
        jti=jti,
        defaults={
            "user_id": user_id,
            "expires_at": expires_at,
        },
    )

    logger.info("Access token revoked")

    # Calculate remaining lifetime.
    remaining_seconds = max(
        int(
            (
                expires_at - datetime.now(timezone.utc)
            ).total_seconds()
        ),
        1,
    )

    # Redis is the fast lookup layer.
    cache.set(
        get_access_revocation_key(jti),
        True,
        timeout=remaining_seconds, # TTL
    )

    logger.info("Revoked Refresh token jti added to redis for fast look up")


def is_access_token_revoked(jti: str) -> bool:
    """
    Redis-first access-token revocation check.

    Redis:
        True  -> revoked
        False -> not revoked

    If Redis fails, PostgreSQL is consulted.
    """

    key = get_access_revocation_key(jti)

    try:
        cached_value = cache.get(key)  # Getting the value of the access token jti from redis. True if it exist None if not
        logger.info("Checking redis to see if refresh jti is revoked")

    except Exception:
        # Redis failure → DB fallback if redis not available.
        logger.info("Checking DB to see if refresh jti is revoked. Because redis not available")
        return RevokedAccessToken.objects.filter(
            jti=jti
        ).exists()
    

    # Redis explicitly says revoked.
    if cached_value is True: 
        return True

    # Cache miss.
    logger.info("Checking DB to see if access jti is revoked. Because redis does not have it")
    revoked = RevokedAccessToken.objects.filter(
        jti=jti
    ).exists()

    # If DB says revoked, repair Redis.
    if revoked:
        # Adding the access jti to redis if it found in the DB
        logger.info("Adding the access jti to redis")

        token = RevokedAccessToken.objects.get(jti=jti)     # Getting more information on the token

        remaining_seconds = max(
            int(
                (
                    token.expires_at - datetime.now(timezone.utc)
                ).total_seconds()
            ),
            1,
        )

        try:
            cache.set(
                key,
                True,
                timeout=remaining_seconds,
            )
            logger.info("Access jti added to redis")
            
        except Exception:
            # DB already contains the authoritative state.
            pass

    return revoked
