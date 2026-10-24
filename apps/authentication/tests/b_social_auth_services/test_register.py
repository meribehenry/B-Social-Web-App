from rest_framework import status
from apps.authentication.services.b_social_auth import BSocialAuthService
from django.contrib.auth import get_user_model
from apps.user.service import ProfileService
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_register_with_right_data(mocker):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    data = {
            "display_name": "Mia Bella Sis",
            "email": "miasis@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    result, _ = BSocialAuthService().register(data)

    assert isinstance(result, dict) == True
    assert result != {}

    user = result["data"].get("user")
    assert result["status_code"] == status.HTTP_201_CREATED
    assert user is not None
    assert user["profile"]["display_name"] == "Mia Bella Sis"
    mock_send_otp_email.assert_called_once()


@pytest.mark.django_db
def test_b_social_auth_service_register_fails_if_user_immediately_re_registers_within_15_minutes(mocker):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    data_1 = {
            "display_name": "Mia Bella Sis",
            "email": "miasis@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    BSocialAuthService().register(data_1)

    mock_send_otp_email.reset_mock()

    data_2 = {
            "display_name": "Mia Bella Sis",
            "email": "miasis@gmail.com",
            "password": "12345678$Mialilsis",
            "confirm_password": "12345678$Mialilsis",
            "gender": "female"
        }  

    result_2, error_2 = BSocialAuthService().register(data_2)

    assert isinstance(error_2, dict) == True
    assert result_2 == {}
    assert error_2 != {}

    assert error_2["status_code"] == status.HTTP_409_CONFLICT
    assert error_2["message"] is not None
    assert error_2["data"] is not None
    assert error_2["data"]["user"]["profile"]["display_name"] == "Mia Bella Sis"
    mock_send_otp_email.assert_not_called()
    assert mock_send_otp_email.call_count != 2


@pytest.mark.django_db
def test_b_social_auth_service_register_fails_if_email_already_exists(mocker, verified_user_data_to_create):
    mock_send_otp_email = mocker.patch("apps.authentication.services.b_social_auth.send_otp_email.delay")

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = verified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **verified_user_data_to_create
    )
    Profile.objects.create(display_name=display_name, user=user)

    data = {
            "display_name": "Mia Bella Sis",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    _, error = BSocialAuthService().register(data)

    assert isinstance(error, dict) == True
    assert error != {}
    assert error["status_code"] == status.HTTP_409_CONFLICT
    mock_send_otp_email.assert_not_called()
