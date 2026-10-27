from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from apps.authentication.models import RevokedAccessToken
from rest_framework_simplejwt.tokens import RefreshToken
import pytest


@pytest.mark.django_db
def test_logout_view_succeeds(
    create_verified_user,
    api_client, 
    mock_app_cache_for_jwt_tokens,
    ):

    user = create_verified_user
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    refresh_token = RefreshToken().for_user(user)
    refresh_token_str = str(refresh_token)
    access_token = refresh_token.access_token
    access_token_str = str(access_token) 
    
    url = reverse("logout")

    api_client.cookies["refresh_token"] = refresh_token_str
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token_str}")

    response = api_client.post(url, content_type="application/json")
    assert response.status_code == status.HTTP_200_OK

    assert jwt_app_cache.get(f"revoked_access:{access_token["jti"]}") == "1"
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token["jti"]}") == "1"

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == True
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == True
