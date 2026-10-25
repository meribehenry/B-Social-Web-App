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