from rest_framework import status
from apps.authentication.models import UserToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from django.contrib.auth import get_user_model
from apps.user.service import ProfileService
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_resend_otp_for_registration_succeeds(mocker, unverified_user_data_to_create):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        email="mia@gmail.com",
        password="password",
        gender="female",
    )
    Profile.objects.create(display_name=display_name, user=user)

    data = {
            "email": "mia@gmail.com",
            "purpose": "REGISTRATION"
        }
    result, _ = BSocialAuthService().resend_OTP(data)

    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert UserToken.objects.filter(email=data["email"], purpose=data["purpose"]).exists()
    mock_send_otp_email.assert_called_once()


@pytest.mark.django_db
def test_b_social_auth_service_resend_otp_for_fails_email_not_sent_due_to_email_not_found(mocker, unverified_user_data_to_create):

    # Test for all purpose
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **unverified_user_data_to_create
    )
    Profile.objects.create(display_name=display_name, user=user)

    data = {
            "email": "mia5@gmail.com",
            "purpose": "REGISTRATION"
        }
    result, _ = BSocialAuthService().resend_OTP(data)

    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert UserToken.objects.filter(email=data["email"], purpose=data["purpose"]).exists() == False
    assert mock_send_otp_email.call_count == 0


@pytest.mark.django_db
def test_b_social_auth_service_resend_otp_for_password_reset_succeeds(mocker, verified_user_data_to_create):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = verified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **verified_user_data_to_create
    )
    Profile.objects.create(display_name=display_name, user=user)

    data = {
            "email": "mia@gmail.com",
            "purpose": "PASSWORD_RESET"
        }
    result, _ = BSocialAuthService().resend_OTP(data)

    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert UserToken.objects.filter(email=data["email"], purpose=data["purpose"]).exists()
    mock_send_otp_email.assert_called_once()