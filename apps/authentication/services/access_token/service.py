from datetime import datetime, timezone
from django.core.cache import cache
from django.db import transaction
from ...models import RevokedAccessToken


def get_access_revocation_key(jti: str) -> str:
    return f"revoked_access:{jti}"


@transaction.atomic
def revoke_access_token_object(token):
    """
    Permanently record the access token as revoked in the DB
    and cache that information in Redis.
    """

    jti = token["jti"]
    user_id = token["user_id"]
    exp = token["exp"]

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

    # Calculate remaining lifetime.
    remaining_seconds = max(
        int(
            (
                expires_at
                - datetime.now(timezone.utc)
            ).total_seconds()
        ),
        1,
    )

    # Redis is the fast lookup layer.
    cache.set(
        get_access_revocation_key(jti),
        True,
        timeout=remaining_seconds,
    )


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
        cached_value = cache.get(key)

    except Exception:
        # Redis failure → DB fallback.
        return RevokedAccessToken.objects.filter(
            jti=jti
        ).exists()

    # Redis explicitly says revoked.
    if cached_value is True:
        return True

    # Cache miss.
    revoked = RevokedAccessToken.objects.filter(
        jti=jti
    ).exists()

    # If DB says revoked, repair Redis.
    if revoked:
        token = RevokedAccessToken.objects.get(jti=jti)

        remaining_seconds = max(
            int(
                (
                    token.expires_at
                    - datetime.now(timezone.utc)
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
        except Exception:
            # DB already contains the authoritative state.
            pass

    return revoked
