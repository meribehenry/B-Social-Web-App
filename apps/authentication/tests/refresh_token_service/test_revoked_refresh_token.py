from apps.authentication.services.refresh_token.service import revoke_refresh_token
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
import pytest



@pytest.mark.django_db
def test_revoke_access_token_object_succeeds(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)

    result = revoke_refresh_token(str(refresh_token))

    assert len(jwt_app_cache.keys("revoked_refresh:*")) == 1
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") == "1"
    outstanding_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert outstanding_token.exists() == True
    assert BlacklistedToken.objects.filter(token=outstanding_token.first().id).exists()
    assert result == True


@pytest.mark.django_db
def test_revoke_access_token_object_fails_return_false_invalid_token(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)

    result = revoke_refresh_token(str(refresh_token)+"!")

    assert len(jwt_app_cache.keys("revoked_refresh:*")) == 0
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") is None
    outstanding_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert outstanding_token.exists() == True
    assert BlacklistedToken.objects.filter(token=outstanding_token.first().id).exists() == False
    assert result == False