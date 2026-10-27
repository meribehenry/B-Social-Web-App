from django.urls import reverse
from rest_framework import status
from apps.authentication.models import UserToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from datetime import datetime, timezone, timedelta
import pytest
import uuid


@pytest.mark.django_db
def test_password_reset_view_succeeds(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    reset_token = str(uuid.uuid4())
    user = create_verified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            reset_token_hash=BSocialAuthService().hash_value(reset_token),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    

    url = reverse("password-reset")
    payload = {
            "email": "mia@gmail.com",
            "new_password": "password123#R",
            "confirm_password": "password123#R",
            "password_reset_token": reset_token
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert len(rate_redis.keys("ratelimit:password-reset:ip:*")) == 1
    assert UserToken.objects.filter(email=user.email, purpose="PASSWORD_RESET").exists() == False

    key = f"ratelimit:password-reset:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 9
    assert jwt_app_cache.get("revoked_access:*") is None


@pytest.mark.django_db
def test_password_reset_view_fails_invalid_or_expired_reset_token(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    reset_token = str(uuid.uuid4())
    user = create_verified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            reset_token_hash=BSocialAuthService().hash_value(reset_token),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    

    url = reverse("password-reset")
    payload = {
            "email": "mia@gmail.com",
            "new_password": "password123#R",
            "confirm_password": "password123#R",
            "password_reset_token": str(uuid.uuid4())
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    data = response.json()

    assert data["status"] == "error"
    assert len(rate_redis.keys("ratelimit:password-reset:ip:*")) == 1
    assert UserToken.objects.filter(email=user.email, purpose="PASSWORD_RESET").exists() == False

    key = f"ratelimit:password-reset:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 9
    assert jwt_app_cache.get("revoked_access:*") is None


@pytest.mark.django_db
def test_password_reset_view_fails_too_many_requests(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    reset_token = str(uuid.uuid4())
    user = create_verified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            reset_token_hash=BSocialAuthService().hash_value(reset_token),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    

    url = reverse("password-reset")
    payload = {
            "email": "mia@gmail.com",
            "new_password": "password123#R",
            "confirm_password": "password123#R",
            "password_reset_token": reset_token
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert len(rate_redis.keys("ratelimit:password-reset:ip:*")) == 1

    key = f"ratelimit:password-reset:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 9

    for _ in range(8):
        api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)


    response_2 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    response_2.status_code = status.HTTP_400_BAD_REQUEST
    data = response_2.json()

    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0


    response_3 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    assert response_3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    data_3 = response_3.json()
    assert data_3["status"] == "error"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0
