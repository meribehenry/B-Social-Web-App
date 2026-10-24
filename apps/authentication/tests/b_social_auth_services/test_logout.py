from pygments.unistring import No
from rest_framework import status
from apps.authentication.models import RevokedAccessToken
from apps.authentication.services.b_social_auth import BSocialAuthService
from apps.user.service import ProfileService
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
import pytest


@pytest.mark.django_db
def test_b_social_auth_service_logout_succeeds(verified_user_data_to_create):
    User = get_user_model()

    User = get_user_model()
    Profile = ProfileService().get_profile_model()

    display_name = verified_user_data_to_create.pop("display_name")
    user = User.objects.create(
        **verified_user_data_to_create
    )

    Profile.objects.create(display_name=display_name, user=user)

    refresh = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh.access_token))
    refresh_token = str(refresh)

    outstanding_refresh_token = OutstandingToken.objects.filter(jti=RefreshToken(refresh_token)["jti"])

    assert outstanding_refresh_token.exists()
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == False
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == False

    result, _ = BSocialAuthService().logout(access_token, refresh_token)
    
    assert isinstance(result, dict) == True
    assert result != {}
    assert result["status_code"] == status.HTTP_200_OK
    assert BlacklistedToken.objects.filter(token=outstanding_refresh_token.first().id).exists() == True
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == True
