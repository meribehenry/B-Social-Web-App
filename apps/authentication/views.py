from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import BSocialTokenRefreshSerializer
from core.logger.logger_client import get_logger


logger = get_logger(__name__)


class TestView(APIView):
    def get(self, request):
        
        # response = Response("Welcome to the party") 
        logger.info("Message", extra={"time": "ol"})
        return Response("Welcome to the party")

class BSocialTokenRefreshView(TokenRefreshView):

    serializer_class = BSocialTokenRefreshSerializer

    def post(self, request, *args, **kwargs):

        refresh_token = request.COOKIES.get(
            "refresh_token"
        )

        if not refresh_token:
            return Response(
                {
                    "detail": "Refresh token not found."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(
            data={
                "refresh": refresh_token
            }
        )

        serializer.is_valid(
            raise_exception=True
        )

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        access_token = request.auth

        refresh_token = request.COOKIES.get(
            "refresh_token"
        )

        # Revoke current access token.
        if access_token:

            # request.auth is a validated SimpleJWT token.
            jti = access_token["jti"]

            from .services.access_token.service import (
                revoke_access_token_object,
            )

            revoke_access_token_object(
                access_token
            )

        # Revoke refresh token.
        if refresh_token:

            from .services.refresh_token.service import (
                revoke_refresh_token,
            )

            revoke_refresh_token(
                refresh_token
            )

        response = Response(
            {
                "detail": "Successfully logged out."
            }
        )

        response.delete_cookie(
            "refresh_token"
        )

        return response


