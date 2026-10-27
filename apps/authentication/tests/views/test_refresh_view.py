from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
import pytest


@pytest.mark.django_db
def test_refresh_view_succeeds(
    create_verified_user,
    api_client, 
    mock_app_cache_for_jwt_tokens,
    mock_rate_limit_redis,
    fake_ip_address
    ):

    user = create_verified_user
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    rate_redis = mock_rate_limit_redis

    refresh_token = RefreshToken().for_user(user)
    refresh_token_str = str(refresh_token)
    
    url = reverse("token-refresh")

    api_client.cookies["refresh_token"] = refresh_token_str

    response = api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    assert response.status_code == status.HTTP_200_OK
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token["jti"]}") == "0"

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False

    key = f"ratelimit:refresh:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 9

    data = response.json()

    assert data["status"] == "success"
    assert data["data"]["access_token"] is not None


@pytest.mark.django_db
def test_refresh_view_fails_invalid_refresh_token(
    create_verified_user,
    api_client, 
    mock_app_cache_for_jwt_tokens,
    mock_rate_limit_redis,
    fake_ip_address
    ):

    user = create_verified_user
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    rate_redis = mock_rate_limit_redis

    refresh_token = RefreshToken().for_user(user)
    refresh_token_str = str(refresh_token)
    
    url = reverse("token-refresh")

    api_client.cookies["refresh_token"] = refresh_token_str + "1"

    response = api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token["jti"]}") is None

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False

    key = f"ratelimit:refresh:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 9

    data = response.json()
    assert data["status"] == "error"


@pytest.mark.django_db
def test_refresh_view_fails_refresh_token_blacklisted(
    create_verified_user,
    api_client, 
    mock_app_cache_for_jwt_tokens,
    mock_rate_limit_redis,
    fake_ip_address
    ):

    user = create_verified_user
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    rate_redis = mock_rate_limit_redis

    refresh_token = RefreshToken().for_user(user)
    refresh_token_str = str(refresh_token)
    refresh_token.blacklist()
    
    url = reverse("token-refresh")

    api_client.cookies["refresh_token"] = refresh_token_str

    response = api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token["jti"]}") is None # Has not been added to redis yet

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == True

    key = f"ratelimit:refresh:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 9

    data = response.json()
    assert data["status"] == "error"


@pytest.mark.django_db
def test_refresh_view_fails_too_many_attempts(
    create_verified_user,
    api_client, 
    mock_app_cache_for_jwt_tokens,
    mock_rate_limit_redis,
    fake_ip_address
    ):

    user = create_verified_user
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    rate_redis = mock_rate_limit_redis

    refresh_token = RefreshToken().for_user(user)
    refresh_token_str = str(refresh_token)
    
    url = reverse("token-refresh")

    api_client.cookies["refresh_token"] = refresh_token_str

    response_1 = api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_1.status_code == status.HTTP_200_OK

    assert jwt_app_cache.get(f"revoked_refresh:{refresh_token["jti"]}") == "0"

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=refresh_token["jti"])
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False

    key = f"ratelimit:refresh:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 9

    data = response_1.json()
    assert data["status"] == "success"

    for _ in range(8):
        api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    response_2 = api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    assert response_2.status_code == status.HTTP_200_OK
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0

    response_3 = api_client.post(url, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0