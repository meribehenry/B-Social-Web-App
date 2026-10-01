from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from ...services.access_token.service import is_access_token_revoked
from core.logger.logger_client import get_logger

logger = get_logger(__name__)



class RevocableJWTAuthentication(JWTAuthentication):
    """ This help check if access token is revoked alongside the normal JWTAuthentication flow"""

    def get_validated_token(self, raw_token):

        # Let SimpleJWT perform all normal JWT validation first.
        validated_token = super().get_validated_token(raw_token)

        jti = validated_token["jti"]

        if is_access_token_revoked(jti):
            logger.info("Access token revoked")
            raise AuthenticationFailed("This access token has been revoked.")
            

        return validated_token
