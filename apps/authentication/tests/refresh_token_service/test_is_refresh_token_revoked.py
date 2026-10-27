from apps.authentication.services.refresh_token.service import is_refresh_token_revoked
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
import pytest



@pytest.mark.django_db
def test_is_refresh_token_revoked_returns_true(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    refresh_token.blacklist()

    result = is_refresh_token_revoked(refresh_token["jti"])

    assert len(jwt_app_cache.keys("revoked_refresh:*")) == 1
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") == "1"
    assert result == True


@pytest.mark.django_db
def test_is_refresh_token_revoked_false(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)

    result = is_refresh_token_revoked(refresh_token["jti"])

    assert len(jwt_app_cache.keys("revoked_refresh:*")) == 1
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") == "0"
    assert result == False