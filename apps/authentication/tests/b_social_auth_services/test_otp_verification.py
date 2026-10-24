from rest_framework import status
from apps.authentication.services.b_social_auth import BSocialAuthService
from apps.authentication.models import UserToken
from apps.user.service import ProfileService
from django.contrib.auth import get_user_model
from datetime import datetime, timezone, timedelta
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_verify_otp_for_registration_succeeds(mocker, unverified_user_data_to_create):
    mock_send_welcome_email = mocker.patch("apps.authentication.services.b_social_auth.send_welcome_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **unverified_user_data_to_create
    )

    Profile.objects.create(display_name=display_name, user=user)

    UserToken.objects.create(
            email=user.email, 
            purpose="REGISTRATION", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    data = {
        "email": "mia@gmail.com",
        "otp": "100100",
        "purpose": "REGISTRATION"
    }

    result, _ = BSocialAuthService().OTP_verification(data)

    assert isinstance(result, dict) == True
    assert result != {}

    result_user = result["data"].get("user")
    assert result["status_code"] == status.HTTP_200_OK
    assert result_user is not None
    assert result_user["profile"]["display_name"] == "Mia Bella"
    mock_send_welcome_email.assert_called_once()
    assert UserToken.objects.filter(email=user.email).first() == None


@pytest.mark.django_db
def test_b_social_auth_service_verify_otp_for_registration_fails_due_to_invalid_otp(mocker, unverified_user_data_to_create):
    mock_send_welcome_email = mocker.patch("apps.authentication.services.b_social_auth.send_welcome_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()
    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **unverified_user_data_to_create
    )

    Profile.objects.create(display_name=display_name, user=user)
    UserToken.objects.create(
            email=user.email, 
            purpose="REGISTRATION", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    data = {
        "email": "mia@gmail.com",
        "otp": "100105",
        "purpose": "REGISTRATION"
    }

    result, error = BSocialAuthService().OTP_verification(data)

    assert isinstance(error, dict) == True
    assert error != {}

    assert error["status_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert error["message"] is not None
    mock_send_welcome_email.assert_not_called()
    assert UserToken.objects.filter(email=user.email).exists()
    assert UserToken.objects.filter(email=user.email).first().attempts == 1


@pytest.mark.django_db
def test_b_social_auth_service_verify_otp_fails_and_token_deleted_after_3_failed_attempts(mocker, unverified_user_data_to_create):
    # This is for all purpose
    mock_send_welcome_email = mocker.patch("apps.authentication.services.b_social_auth.send_welcome_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
            **unverified_user_data_to_create
        )
    
    Profile.objects.create(display_name=display_name, user=user)
    UserToken.objects.create(
            email=user.email, 
            purpose="REGISTRATION",         
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    data = {
        "email": "mia@gmail.com",
        "otp": "100105",
        "purpose": "REGISTRATION"
    }

    _, error = BSocialAuthService().OTP_verification(data)

    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert error["message"] is not None
    mock_send_welcome_email.assert_not_called()
    assert UserToken.objects.filter(email=user.email).exists()
    assert UserToken.objects.filter(email=user.email).first().attempts == 1

    _, error = BSocialAuthService().OTP_verification(data)
    assert UserToken.objects.filter(email=user.email).exists()
    assert UserToken.objects.filter(email=user.email).first().attempts == 2

    _, error = BSocialAuthService().OTP_verification(data)
    assert UserToken.objects.filter(email=user.email).exists()
    assert UserToken.objects.filter(email=user.email).first().attempts == 3

    _, error = BSocialAuthService().OTP_verification(data)
    assert UserToken.objects.filter(email=user.email).exists() == False


@pytest.mark.django_db
def test_b_social_auth_service_verify_otp_for_registration_fails_due_to_wrong_purpose(mocker, unverified_user_data_to_create):
    # This is for all purpose
    mock_send_welcome_email = mocker.patch("apps.authentication.services.b_social_auth.send_welcome_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **unverified_user_data_to_create
    )

    Profile.objects.create(display_name=display_name, user=user)
    UserToken.objects.create(
            email=user.email, 
            purpose="REGISTRATION", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    data = {
        "email": "mia@gmail.com",
        "otp": "100100",
        "purpose": "PASSWORD_RESET"
    }

    _, error = BSocialAuthService().OTP_verification(data)

    assert isinstance(error, dict) == True
    assert error != {}

    assert error["status_code"] == status.HTTP_400_BAD_REQUEST
    assert error["message"] is not None
    mock_send_welcome_email.assert_not_called()
    assert UserToken.objects.filter(email=user.email).exists()


@pytest.mark.django_db
def test_b_social_auth_service_verify_otp_for_password_reset_succeeds(verified_user_data_to_create):

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = verified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **verified_user_data_to_create
    )

    Profile.objects.create(display_name=display_name, user=user)
    UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            otp_hash=BSocialAuthService().hash_value("100100"),
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )

    data = {
        "email": "mia@gmail.com",
        "otp": "100100",
        "purpose": "PASSWORD_RESET"
    }

    result, _ = BSocialAuthService().OTP_verification(data)

    assert isinstance(result, dict) == True
    assert result != {}

    assert result["status_code"] == status.HTTP_200_OK
    assert result["data"]["reset_token"] is not None
    assert UserToken.objects.filter(email=user.email).exists()
    token = UserToken.objects.filter(email=user.email).first()
    assert token.attempts == 0
    assert token.otp_hash is None