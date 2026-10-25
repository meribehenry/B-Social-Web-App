from django.urls import reverse
import pytest
from rest_framework import status


@pytest.mark.django_db
def test_registration_view_succeeds(mocker, api_client, mock_rate_limit_redis):

    rate_redis = mock_rate_limit_redis
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    url = reverse("register")
    payload = {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    
    response = api_client.post(url, data=payload, content_type="application/json")
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()

    assert data["status"] == "success"
    assert data["data"] is not None
    assert data["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    assert len(rate_redis.keys("ratelimit:register:ip:*")) == 1
    mock_send_otp_email.assert_called_once()


@pytest.mark.django_db
def test_registration_view_fails_email_already_exists(
    mocker, 
    api_client, 
    mock_rate_limit_redis, 
    fake_ip_address
    ):

    rate_redis = mock_rate_limit_redis
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    url = reverse("register")
    payload = {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    
    response_1 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_1.status_code == status.HTTP_201_CREATED
    
    data_1 = response_1.json()

    assert data_1["status"] == "success"
    assert data_1["data"] is not None
    assert data_1["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    assert len(rate_redis.keys("ratelimit:register:ip:*")) == 1

    key = f"ratelimit:register:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4
    mock_send_otp_email.assert_called_once()


    response_2 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_2.status_code == status.HTTP_409_CONFLICT
    
    data_2 = response_2.json()

    assert data_2["status"] == "error"
    assert data_2["data"] is not None
    assert data_2["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 3
    assert mock_send_otp_email.call_count == 1


@pytest.mark.django_db
def test_registration_view_fails_too_many_requests(
    mocker, 
    api_client, 
    mock_rate_limit_redis, 
    fake_ip_address
    ):

    rate_redis = mock_rate_limit_redis
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    url = reverse("register")
    payload = {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    
    response_1 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_1.status_code == status.HTTP_201_CREATED
    
    data_1 = response_1.json()

    assert data_1["status"] == "success"
    assert data_1["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    assert len(rate_redis.keys("ratelimit:register:ip:*")) == 1

    key = f"ratelimit:register:ip:{fake_ip_address}"
    token_int = int(float(rate_redis.hget(key, "tokens")))

    assert token_int == 4
    mock_send_otp_email.assert_called_once()


    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)

    response_2 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_2.status_code == status.HTTP_409_CONFLICT
    
    data_2 = response_2.json()

    assert data_2["status"] == "error"
    assert data_2["data"] is not None
    assert data_2["data"]["user"]["profile"]["display_name"] == "Mia Bella"
    
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0

    response_3 = api_client.post(url, data=payload, content_type="application/json", HTTP_X_FORWARDED_FOR=fake_ip_address)
    assert response_3.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    data_3 = response_3.json()

    assert data_3["status"] == "error"
    assert data_3.get("data") is None
    
    token_int = int(float(rate_redis.hget(key, "tokens")))
    assert token_int == 0