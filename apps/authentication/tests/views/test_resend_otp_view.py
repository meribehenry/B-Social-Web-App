from django.urls import reverse
import pytest
from rest_framework import status


@pytest.mark.django_db
def test_resend_otp_view_succeeds(mocker, api_client, mock_rate_limit_redis, fake_ip_address, create_unverified_user):

    rate_redis = mock_rate_limit_redis
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    url = reverse("resend-otp")
    payload = {
            "email": "mia@gmail.com",
            "purpose": "REGISTRATION"
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert len(rate_redis.keys("ratelimit:resend-otp:ip:*")) == 1
    mock_send_otp_email.assert_called_once()

    key = f"ratelimit:resend-otp:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4


@pytest.mark.django_db
def test_resend_otp_view_fails_email_not_found(mocker, api_client, mock_rate_limit_redis, fake_ip_address, create_unverified_user):

    rate_redis = mock_rate_limit_redis
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    url = reverse("resend-otp")
    payload = {
            "email": "mia5@gmail.com",
            "purpose": "REGISTRATION"
        }
    
    response = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()

    assert data["status"] == "success"
    assert len(rate_redis.keys("ratelimit:resend-otp:ip:*")) == 1
    mock_send_otp_email.assert_not_called()

    key = f"ratelimit:resend-otp:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4


@pytest.mark.django_db
def test_resend_otp_view_fails_too_many_requests(mocker, api_client, mock_rate_limit_redis, fake_ip_address, create_unverified_user):

    rate_redis = mock_rate_limit_redis
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    url = reverse("resend-otp")
    payload = {
            "email": "mia5@gmail.com",
            "purpose": "REGISTRATION"
        }
    
    response_1 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_1.status_code == status.HTTP_200_OK
    
    data = response_1.json()

    assert data["status"] == "success"
    assert len(rate_redis.keys("ratelimit:resend-otp:ip:*")) == 1
    mock_send_otp_email.assert_not_called()

    key = f"ratelimit:resend-otp:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4

    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)


    response_2 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    data = response_2.json()
    assert data["status"] == "success"

    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0


    response_3 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    assert response_3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    data_3 = response_3.json()
    assert data_3["status"] == "error"
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0