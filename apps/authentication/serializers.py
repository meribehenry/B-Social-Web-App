from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)

from .services.refresh_token.service import (
    is_refresh_token_revoked,
)


class BSocialTokenRefreshSerializer(
    TokenRefreshSerializer
):

    def validate(self, attrs):

        refresh = self.token_class(
            attrs["refresh"]
        )

        jti = refresh["jti"]

        if is_refresh_token_revoked(jti):
            raise AuthenticationFailed(
                "This refresh token has been revoked."
            )

        # SimpleJWT now performs its normal refresh flow.
        return super().validate(attrs)
