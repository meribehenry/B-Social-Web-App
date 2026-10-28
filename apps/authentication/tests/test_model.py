from apps.authentication.models import UserToken
from datetime import datetime, timezone, timedelta
import pytest


@pytest.mark.django_db
def test_is_exipired_method_in_UserToken_model(create_unverified_user):
    user = create_unverified_user
    
    user_token = UserToken.objects.create(
        email=user.email, 
        purpose="PASSWORD_RESET", 
        otp_hash="100100",  # This is just a demo otp_hash
        expires_at= datetime.now(timezone.utc) - timedelta(minutes=11)
    )

    assert user_token.is_expired()
    user_token.delete()

    user_token = UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            otp_hash="100100",  # This is just a demo otp_hash
            expires_at= datetime.now(timezone.utc) + timedelta(minutes=10)
        )
    
    assert user_token.is_expired() == False



