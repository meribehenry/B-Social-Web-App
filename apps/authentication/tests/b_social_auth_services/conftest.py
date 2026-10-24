from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
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