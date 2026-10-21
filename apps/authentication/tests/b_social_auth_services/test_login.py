from pygments.unistring import No
from rest_framework import status
from django.contrib.auth.hashers import make_password
from apps.authentication.services.b_social_auth import BSocialAuthService
from apps.user.service import ProfileService
from django.contrib.auth import get_user_model
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_login_succeeds():
    User = get_user_model()

    User = get_user_model()
    Profile = ProfileService().get_profile_model()
    user = User.objects.create(
        email="mia@gmail.com",
        password=make_password("password123$"),
        gender="female",
        email_verified=True,
        status="active",
        is_active=True,
    )

    Profile.objects.create(display_name="Mia Bella", user=user)

    data = {
        "email": "mia@gmail.com",
        "password": "password123$",
    }
    result, _ = BSocialAuthService().login(data)
    
    assert isinstance(result, dict) == True
    assert result != {}

    user = result["data"].get("user")
    assert result["status_code"] == status.HTTP_200_OK
    assert user is not None
    assert user["profile"]["display_name"] == "Mia Bella"
    assert result["data"]["access_token"] is not None
    assert result["data"]["refresh_token"] is not None


@pytest.mark.django_db
def test_b_social_auth_service_login_fails_if_email_does_not_exists_or_password_incorrect():
    User = get_user_model()

    User = get_user_model()
    Profile = ProfileService().get_profile_model()
    user = User.objects.create(
        email="mia@gmail.com",
        password=make_password("password123$"),
        gender="female",
        email_verified=True,
        status="active",
        is_active=True,
    )

    Profile.objects.create(display_name="Mia Bella", user=user)

    data = {
        "email": "mia3@gmail.com",
        "password": "password1234$",
    }
    result, error = BSocialAuthService().login(data)
    
    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_401_UNAUTHORIZED
    assert error["message"] is not None
