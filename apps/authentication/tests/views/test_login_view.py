from django.urls import reverse
from rest_framework import status
import pytest


@pytest.mark.django_db
def test_login_view_succeeds(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    user = create_verified_user
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    

    url = reverse("login")
    payload = {
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert data["data"] is not None
    assert data["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    assert len(rate_redis.keys("ratelimit:login:ip:*")) == 1
    key = f"ratelimit:login:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4
    assert jwt_app_cache.get("revoked_access:*") is None


@pytest.mark.django_db
def test_login_view_fails_invalid_credentials(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    user = create_verified_user
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    

    url = reverse("login")
    payload = {
            "email": "mia5@gmail.com",
            "password": "123456789$Mia",
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    data = response.json()

    assert data["status"] == "error"
    assert len(rate_redis.keys("ratelimit:login:ip:*")) == 1
    key = f"ratelimit:login:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4
    assert jwt_app_cache.get("revoked_access:*") is None


@pytest.mark.django_db
def test_login_view_fails_too_many_requests(
    api_client, 
    mock_rate_limit_redis, 
    fake_ip_address,
    create_verified_user
    ):

    user = create_verified_user

    rate_redis = mock_rate_limit_redis

    url = reverse("login")
    payload = {
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
        }
    
    response_1 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_1.status_code == status.HTTP_200_OK
    
    data_1 = response_1.json()

    assert data_1["status"] == "success"
    assert data_1["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    assert len(rate_redis.keys("ratelimit:login:ip:*")) == 1

    key = f"ratelimit:login:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4

    payload["email"] = "kia@gmail.com"
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    response_2 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_2.status_code == status.HTTP_401_UNAUTHORIZED
    
    data_2 = response_2.json()

    assert data_2["status"] == "error"
    
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0

    response_3 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    data_3 = response_3.json()

    assert data_3["status"] == "error"
    assert data_3.get("data") is None
    
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0