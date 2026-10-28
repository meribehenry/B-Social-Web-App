from apps.authentication.serializers import validate_password


def test_validate_password_passess():
    data = {
        "password": "123456784Hen",
        "confirm_password": "123456784Hen",
    }

    result = validate_password(data)

    assert result == data



