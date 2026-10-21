from django.contrib.auth import get_user_model
import pytest

User = get_user_model()

@pytest.fixture
def user():
    data =  {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "confirm_password": "12345678$Mia",
            "gender": "female"
        }
    return data