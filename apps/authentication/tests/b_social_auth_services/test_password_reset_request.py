from rest_framework import status
from apps.authentication.models import UserToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from django.contrib.auth import get_user_model
from apps.user.service import ProfileService
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_password_reset_request_succeeds(mocker, create_verified_user):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    user = create_verified_user

    data = {
            "email": "mia@gmail.com",
        }
    result, _ = BSocialAuthService().password_reset_request(data)

    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert UserToken.objects.filter(email=data["email"], purpose="PASSWORD_RESET").exists()
    mock_send_otp_email.assert_called_once()


@pytest.mark.django_db
def test_b_social_auth_service_password_reset_request_fails_due_to_unverified_account(mocker, create_unverified_user):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    user = create_unverified_user

    data = {
            "email": "mia@gmail.com",
        }
    _, error = BSocialAuthService().password_reset_request(data)

    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_400_BAD_REQUEST
    assert UserToken.objects.filter(email=data["email"], purpose="PASSWORD_RESET").exists() == False
    mock_send_otp_email.assert_not_called()


@pytest.mark.django_db
def test_b_social_auth_service_password_reset_request_email_not_sent_due_to_email_not_found(mocker, create_verified_user):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    user = create_verified_user

    data = {
            "email": "mia5@gmail.com",
        }
    result, _ = BSocialAuthService().password_reset_request(data)

    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert UserToken.objects.filter(email=data["email"], purpose="PASSWORD_RESET").exists() == False
    mock_send_otp_email.assert_not_called()