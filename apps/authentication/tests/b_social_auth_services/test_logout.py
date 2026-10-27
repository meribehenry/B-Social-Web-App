from rest_framework import status
from apps.authentication.models import RevokedAccessToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_logout_succeeds(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh_token.access_token))
    refresh_token_str = str(refresh_token)

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])

    assert outstanding_refresh_token.exists()
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == False

    result, _ = BSocialAuthService().logout(access_token, refresh_token_str)
    
    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == True
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == True

    assert len(jwt_app_cache.keys("revoked_access:*")) == 1
    assert len(jwt_app_cache.keys("revoked_refresh:*")) == 1
    assert jwt_app_cache.get(f"revoked_access:{access_token['jti']}") == "1"
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") == "1"


@pytest.mark.django_db
def test_b_social_auth_service_logout_fails_refresh_token_invalid(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh_token.access_token))
    refresh_token_str = str(refresh_token) + "1"

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])

    assert outstanding_refresh_token.exists()
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == False

    _, error = BSocialAuthService().logout(access_token, refresh_token_str)
    
    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_400_BAD_REQUEST
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == False

    assert jwt_app_cache.get(f"revoked_access:{access_token['jti']}") is None
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") is None


@pytest.mark.django_db
def test_b_social_auth_service_logout_fails_refresh_token_blacklisted(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh_token.access_token))
    refresh_token_str = str(refresh_token)
    refresh_token.blacklist()

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])

    assert outstanding_refresh_token.exists()
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == True
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == False

    _, error = BSocialAuthService().logout(access_token, refresh_token_str)
    
    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_400_BAD_REQUEST
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == False

    assert jwt_app_cache.get(f"revoked_access:{access_token['jti']}") is None
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token['jti']}") is None