from datetime import datetime, timezone
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken


def get_refresh_revocation_key(jti: str) -> str:
    return f"revoked_refresh:{jti}"


def revoke_refresh_token(token_string: str):

    token = RefreshToken(token_string)

    jti = token["jti"]

    # SimpleJWT's official blacklist system.
    token.blacklist()

    # Calculate remaining lifetime.
    expires_at = datetime.fromtimestamp(
        token["exp"],
        tz=timezone.utc,
    )

    remaining_seconds = max(
        int(
            (
                expires_at
                - datetime.now(timezone.utc)
            ).total_seconds()
        ),
        1,
    )

    # Redis acceleration.
    cache.set(
        get_refresh_revocation_key(jti),
        True,
        timeout=remaining_seconds,
    )


from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


def is_refresh_token_revoked(jti: str) -> bool:

    key = get_refresh_revocation_key(jti)

    try:
        cached_value = cache.get(key)

    except Exception:
        # Redis failure → SimpleJWT database.
        return BlacklistedToken.objects.filter(
            token__jti=jti
        ).exists()

    if cached_value is True:
        return True

    # Redis miss → authoritative DB check.
    revoked = BlacklistedToken.objects.filter(
        token__jti=jti
    ).exists()

    if revoked:
        try:
            outstanding = OutstandingToken.objects.get(
                jti=jti
            )

            remaining_seconds = max(
                int(
                    (
                        outstanding.expires_at
                        - datetime.now(timezone.utc)
                    ).total_seconds()
                ),
                1,
            )

            cache.set(
                key,
                True,
                timeout=remaining_seconds,
            )

        except Exception:
            pass