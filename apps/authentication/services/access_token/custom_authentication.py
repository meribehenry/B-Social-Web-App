from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from ...services.access_token.service import is_access_token_revoked



class RevocableJWTAuthentication(JWTAuthentication):

    def get_validated_token(self, raw_token):

        # Let SimpleJWT perform all normal JWT validation first.
        validated_token = super().get_validated_token(
            raw_token
        )

        jti = validated_token["jti"]

        if is_access_token_revoked(jti):
            raise AuthenticationFailed(
                "This access token has been revoked."
            )

        return validated_token
