from apps.authentication.models import RevokedAccessToken
from apps.authentication.services.access_token.service import  is_access_token_revoked
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from apps.authentication.models import RevokedAccessToken
from datetime import datetime, timezone
import pytest


@pytest.mark.django_db
def test_is_access_token_revoked_returns_true(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh_token.access_token))

    expires_at = datetime.fromtimestamp(
        access_token["exp"],
        tz=timezone.utc,
    )

    RevokedAccessToken.objects.create(jti=access_token["jti"], expires_at=expires_at, user=user)

    result = is_access_token_revoked(access_token)

    assert len(jwt_app_cache.keys("revoked_access:*")) == 1
    assert jwt_app_cache.get(f"revoked_access:{access_token['jti']}") == "1"
    assert result == True


@pytest.mark.django_db
def test_is_access_token_revoked_returns_false(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh_token.access_token))

    result = is_access_token_revoked(access_token)

    assert len(jwt_app_cache.keys("revoked_access:*")) == 1
    assert jwt_app_cache.get(f"revoked_access:{access_token['jti']}") == "0"
    assert result == False