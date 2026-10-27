from datetime import datetime, timezone
from django.db.models import Q
from core.clients.redis_client import get_app_redis_client
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken, Token
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

    app_cache = get_app_redis_client()

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
    app_cache.set(
        get_access_revocation_key(jti),
        1,
        ex=remaining_seconds, # TTL
    )

    logger.info("Revoked Refresh token jti added to redis for fast look up")


def is_access_token_revoked(access_token: Token) -> bool:
    """
    Redis-first access-token revocation check.

    Redis:
        True  -> revoked
        False -> not revoked

    If Redis fails, PostgreSQL is consulted.
    """
    jti = access_token["jti"]

    app_cache = get_app_redis_client()

    key = get_access_revocation_key(jti)

    try:
        cached_value = app_cache.get(key)  # Getting the value of the access token jti from redis. True if it exist None if not
        logger.info("Checking redis to see if refresh jti is revoked")

    except Exception:
        # Redis failure → DB fallback if redis not available.
        logger.info("Checking DB to see if refresh jti is revoked. Because redis not available")
        return RevokedAccessToken.objects.filter(
            jti=jti
        ).exists()
    

    # Redis explicitly says revoked.
    if cached_value == "1": 
        return True

    # Cache miss.
    logger.info("Checking DB to see if access jti is revoked. Because redis does not have it")

    revoked = RevokedAccessToken.objects.filter(
        jti=jti
    ).exists()

    token = RevokedAccessToken.objects.filter(jti=jti).first() # Getting more information on the token

    expires_at = token.expires_at if token else datetime.fromtimestamp(access_token["exp"], tz=timezone.utc)
    
    # Calculating token remaining seconds
    remaining_seconds = max(
            int(
                (
                    expires_at - datetime.now(timezone.utc)
                ).total_seconds()
            ),
            1,
        )

    try:
        logger.info("Adding the access jti to redis")
        
        if revoked:  
            # Adding the access jti to redis as revoked if it found in the DB. 
            app_cache.set(
                key,
                1,
                ex=remaining_seconds,
            )
            logger.info("Revoked access jti added to redis")

        else:
            # Adding vaild access jti to redis for easier look up next time
            app_cache.set(
                key,
                0,
                ex=remaining_seconds,
            )
            logger.info("Access jti added to redis but not revoked")
            
    except Exception:
        # DB already contains the authoritative state.
        logger.info("Error access jti not added to redis. Perphaps redis is down")
        pass

    return revoked
