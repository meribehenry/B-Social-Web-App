from django.urls import reverse
from rest_framework import status
from apps.authentication.models import UserToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from datetime import datetime, timezone, timedelta
import pytest


@pytest.mark.django_db
def test_otp_verification_view_succeeds_for_registration(
    mocker,
    create_unverified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    user = create_unverified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="REGISTRATION", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    mock_send_welcome_email = mocker.patch("apps.authentication.services.b_social_auth.send_welcome_email.delay")
    

    url = reverse("otp-verification")
    payload = {
            "email": "mia@gmail.com",
            "purpose": "REGISTRATION",
            "otp": "100100"
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert data["data"] is not None
    assert data["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    assert len(rate_redis.keys("ratelimit:otp-verification:ip:*")) == 1
    key = f"ratelimit:otp-verification:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 2
    assert jwt_app_cache.get("revoked_access:*") is None
    mock_send_welcome_email.assert_called_once()


@pytest.mark.django_db
def test_otp_verification_view_succeeds_for_password_reset(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    user = create_verified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    

    url = reverse("otp-verification")
    payload = {
            "email": "mia@gmail.com",
            "purpose": "PASSWORD_RESET",
            "otp": "100100"
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert data["data"] is not None
    assert data["data"]["reset_token"] is not None
    assert len(rate_redis.keys("ratelimit:otp-verification:ip:*")) == 1
    key = f"ratelimit:otp-verification:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 2
    assert jwt_app_cache.get("revoked_access:*") is None


@pytest.mark.django_db
def test_otp_verification_view_fails_expired_or_invalid_otp(
    create_verified_user,
    api_client, 
    mock_rate_limit_redis, 
    mock_app_cache_for_jwt_tokens,
    fake_ip_address
    ):

    user = create_verified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    rate_redis = mock_rate_limit_redis
    jwt_app_cache = mock_app_cache_for_jwt_tokens
    
    url = reverse("otp-verification")
    payload = {
            "email": "mia@gmail.com",
            "purpose": "PASSWORD_RESET",
            "otp": "100101"
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    data = response.json()

    assert data["status"] == "error"
    assert data.get("data") is None
    assert len(rate_redis.keys("ratelimit:otp-verification:ip:*")) == 1
    key = f"ratelimit:otp-verification:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 2
    assert jwt_app_cache.get("revoked_access:*") is None
    assert UserToken.objects.filter(email=user.email).first().attempts == 1 


@pytest.mark.django_db
def test_otp_verification_view_fails_too_many_requests(
    api_client, 
    mock_rate_limit_redis, 
    fake_ip_address,
    create_verified_user
    ):

    user = create_verified_user
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    rate_redis = mock_rate_limit_redis

    url = reverse("otp-verification")
    payload = {
            "email": "mia@gmail.com",
            "purpose": "PASSWORD_RESET",
            "otp": "100100"
        }
    
    response_1 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_1.status_code == status.HTTP_200_OK
    
    data_1 = response_1.json()


    assert data_1["status"] == "success"
    assert data_1["data"] is not None
    assert data_1["data"]["reset_token"] is not None
    assert len(rate_redis.keys("ratelimit:otp-verification:ip:*")) == 1
    key = f"ratelimit:otp-verification:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 2


    payload["email"] = "kia@gmail.com" # Email doesn't exist so it throws 400
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    response_2 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    
    data_2 = response_2.json()

    assert data_2["status"] == "error"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0


    response_3 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    data_3 = response_3.json()

    assert data_3["status"] == "error"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0