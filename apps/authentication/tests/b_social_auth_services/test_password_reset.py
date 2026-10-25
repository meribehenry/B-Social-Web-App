from rest_framework import status
from apps.authentication.models import UserToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from django.contrib.auth import get_user_model
from apps.user.service import ProfileService
from datetime import datetime, timezone, timedelta
import pytest
import uuid


@pytest.mark.django_db
def test_b_social_auth_service_password_reset_succeeds(create_verified_user):
    reset_token = str(uuid.uuid4())

    user = create_verified_user

    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            reset_token_hash=BSocialAuthService().hash_value(reset_token),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    data = {
            "email": "mia@gmail.com",
            "new_password": "password123#R",
            "confirm_password": "password123#R",
            "password_reset_token": reset_token
        }
    result, _ = BSocialAuthService().password_reset(data)

    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert UserToken.objects.filter(email=data["email"], purpose="PASSWORD_RESET").exists() == False


@pytest.mark.django_db
def test_b_social_auth_service_password_reset_fails_due_to_expired_token(create_verified_user):
    reset_token = str(uuid.uuid4())

    user = create_verified_user

    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            reset_token_hash=BSocialAuthService().hash_value(reset_token),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=0)
        )

    data = {
            "email": "mia@gmail.com",
            "new_password": "password123#R",
            "confirm_password": "password123#R",
            "password_reset_token": reset_token
        }
    _, error = BSocialAuthService().password_reset(data)

    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert UserToken.objects.filter(email=data["email"], purpose="PASSWORD_RESET").exists() == False


@pytest.mark.django_db
def test_b_social_auth_service_password_reset_fails_due_to_invalid_token(create_verified_user):
    reset_token = str(uuid.uuid4())

    user = create_verified_user
    
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            reset_token_hash=BSocialAuthService().hash_value(reset_token),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=0)
        )

    data = {
            "email": "mia@gmail.com",
            "new_password": "password123#R",
            "confirm_password": "password123#R",
            "password_reset_token": str(uuid.uuid4())
        }
    _, error = BSocialAuthService().password_reset(data)

    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert UserToken.objects.filter(email=data["email"], purpose="PASSWORD_RESET").exists() == False