from datetime import datetime, timedelta, timezone
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.tasks.clean_up_tasks import (
                                                    delete_expired_otp_or_reset_token, 
                                                    delete_unverified_user, 
                                                    delete_expired_access_token, 
                                                    delete_expired_refresh_token
                                                )
from django.contrib.auth import get_user_model
from apps.user.service import ProfileService
from apps.authentication.models import RevokedAccessToken, UserToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import pytest



@pytest.mark.django_db
def test_delete_unverified_user_succeeds():
    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    data =[  
          
          {
            "display_name": "Meribe Henry",
            "email": "marsboy409@gmail@gmail.com",
            "password": "12345678$Hen",
            "gender": "male",
            "username": "MeribeHenry"
        },
        {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "gender": "female",
            "username": "miabella"
        }
    ]

    for d in data:
        display_name = d.pop("display_name")

        user = User.objects.create(**d)
        user.date_joined = datetime.now(timezone.utc) - timedelta(minutes=30)    
        user.save(update_fields=["date_joined"])

        Profile.objects.create(display_name=display_name, user=user)

    assert User.objects.all().count() == 2

    delete_unverified_user()

    assert User.objects.all().count() == 0


@pytest.mark.django_db
def test_delete_expired_otp_or_reset_token_succeeds():
    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    data =[  
          
          {
            "display_name": "Meribe Henry",
            "email": "marsboy409@gmail@gmail.com",
            "password": "12345678$Hen",
            "gender": "male",
            "username": "MeribeHenry"
        },
        {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "gender": "female",
            "username": "miabella"
        }
    ]

    for d in data:
        display_name = d.pop("display_name")
        
        user = User.objects.create(**d)

        Profile.objects.create(display_name=display_name, user=user)
        
        UserToken.objects.create(
            email=user.email, 
            purpose="PASSWORD_RESET", 
            otp_hash="100100",  # This is just a demo otp_hash
            expires_at= datetime.now(timezone.utc) - timedelta(minutes=11)
        )

    assert UserToken.objects.all().count() == 2

    delete_expired_otp_or_reset_token()

    assert UserToken.objects.all().count() == 0


@pytest.mark.django_db
def test_delete_expired_access_token_succeeds():
    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    data =[  
          
          {
            "display_name": "Meribe Henry",
            "email": "marsboy409@gmail@gmail.com",
            "password": "12345678$Hen",
            "gender": "male",
            "username": "MeribeHenry"
        },
        {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "gender": "female",
            "username": "miabella"
        }
    ]

    for d in data:
        display_name = d.pop("display_name")
        
        user = User.objects.create(**d)

        Profile.objects.create(display_name=display_name, user=user)

        access_token = RefreshToken().for_user(user)

        expires_at = datetime.fromtimestamp(
            access_token["exp"],
            tz=timezone.utc,
        )
        access_token =RefreshToken().for_user(user).access_token

        token_obj = RevokedAccessToken.objects.create(jti=access_token["jti"], expires_at=expires_at, user=user)
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        token_obj.save(update_fields=["expires_at"])

    assert RevokedAccessToken.objects.all().count() == 2

    delete_expired_access_token()

    assert RevokedAccessToken.objects.all().count() == 0


@pytest.mark.django_db
def test_delete_expired_refresh_token_succeeds():
    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    data =[  
          
          {
            "display_name": "Meribe Henry",
            "email": "marsboy409@gmail@gmail.com",
            "password": "12345678$Hen",
            "gender": "male",
            "username": "MeribeHenry"
        },
        {
            "display_name": "Mia Bella",
            "email": "mia@gmail.com",
            "password": "12345678$Mia",
            "gender": "female",
            "username": "miabella"
        }
    ]

    for d in data:
        display_name = d.pop("display_name")
        
        user = User.objects.create(**d)

        Profile.objects.create(display_name=display_name, user=user)

        refresh_token = RefreshToken().for_user(user)
        refresh_token.blacklist()
        OutstandingToken.objects.all().update(expires_at=datetime.now(timezone.utc) - timedelta(days=365))

        
    assert OutstandingToken.objects.all().count() == 2
    assert BlacklistedToken.objects.all().count() == 2

    delete_expired_refresh_token()

    assert OutstandingToken.objects.all().count() == 0
    assert BlacklistedToken.objects.all().count() == 0