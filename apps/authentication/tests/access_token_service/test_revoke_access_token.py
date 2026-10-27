from apps.authentication.models import RevokedAccessToken
from apps.authentication.services.access_token.service import revoke_access_token_object
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
import pytest


@pytest.mark.django_db
def test_revoke_access_token_object_succeeds(create_verified_user, mock_app_cache_for_jwt_tokens):
    jwt_app_cache = mock_app_cache_for_jwt_tokens

    user = create_verified_user

    refresh_token = RefreshToken().for_user(user)
    access_token = AccessToken(str(refresh_token.access_token))

    revoke_access_token_object(access_token)

    assert len(jwt_app_cache.keys("revoked_access:*")) == 1
    assert jwt_app_cache.get(f"revoked_access:{access_token['jti']}") == "1"
    assert RevokedAccessToken.objects.filter(jti=access_token["jti"]).exists() == True