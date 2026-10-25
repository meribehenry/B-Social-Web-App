from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from apps.user.service import ProfileService
import pytest

User = get_user_model()

@pytest.fixture
def unverified_user_data_to_create():
    data =  {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": make_password("12345678$Mia"),
            "gender": "female"
        }
    return data


@pytest.fixture
def verified_user_data_to_create():
    data =  {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": make_password("12345678$Mia"),
            "gender": "female",
            "email_verified": True,
            "status": "active",
            "is_active": True,
        }
    return data


@pytest.fixture()
def create_verified_user(verified_user_data_to_create):
    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = verified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **verified_user_data_to_create
    )
    Profile.objects.create(display_name=display_name, user=user)

    return user


@pytest.fixture()
def create_unverified_user(unverified_user_data_to_create):
    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = unverified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **unverified_user_data_to_create
    )
    Profile.objects.create(display_name=display_name, user=user)

    return user