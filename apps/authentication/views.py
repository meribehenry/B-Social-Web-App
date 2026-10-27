from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import BSocialTokenRefreshSerializer
from .services.b_social_auth import BSocialAuthService
from core.response import APISuccessResponseHandler, APIErrorResponseHandler
from time import time
from core.logger.logger_client import get_logger
from . import throttle



api_success_response_handler = APISuccessResponseHandler()
api_error_response_handler = APIErrorResponseHandler()
logger = get_logger(__name__)

class TestView(APIView):
    permission_classes = []

    def get(self, request):
        start_time = time()

        # send_welcome_email.delay()

        return Response("Welcome to the party")


class RegristrationView(APIView):
    throttle_classes = [throttle.RegisterTokenBucketThrottle]

    def post(self, request):
        print("here")
        b_social_auth_service = BSocialAuthService()
        result, error = b_social_auth_service.register(request.data)

        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
                data = error.get("data", {})
            )

        return api_success_response_handler.success(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data")
            )


class LoginView(APIView):
    throttle_classes = [throttle.LoginTokenBucketThrottle]

    def post(self, request):
        b_social_auth_service = BSocialAuthService()
        result, error = b_social_auth_service.login(request.data)

        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
                data = error.get("data", {})
            )
        refresh_token = result.get("data").pop("refresh_token")

        return api_success_response_handler.success_extra_data_cookie(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data"),
                name = "refresh_token",
                value = refresh_token
            )


class VerifyOTPView(APIView):
    throttle_classes = [throttle.OTPVerificationTokenBucketThrottle]

    def post(self, request):
        b_social_auth_service = BSocialAuthService()
        result, error = b_social_auth_service.OTP_verification(request.data)

        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
            )

        if result.get("data").get("reset_token"):
            return api_success_response_handler.success(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data")
            )
    

        refresh_token = result.get("data").pop("refresh_token")

        return api_success_response_handler.success_extra_data_cookie(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data"),
                name = "refresh_token",
                value = refresh_token
            )
    

class ResendOTPView(APIView):
    throttle_classes = [throttle.ResendOTPTokenBucketThrottle]

    def post(self, request):
        b_social_auth_service = BSocialAuthService()
        result, error = b_social_auth_service.resend_OTP(request.data)

        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
            )

        return api_success_response_handler.success(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data")
            )
    

class PasswordResetRequestView(APIView):
    throttle_classes = [throttle.PasswordResetRequestTokenBucketThrottle]

    def post(self, request):
        b_social_auth_service = BSocialAuthService()
        result, error = b_social_auth_service.password_reset_request(request.data)

        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
            )

        return api_success_response_handler.success(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data")
            )
    

class PasswordResetView(APIView):
    throttle_classes = [throttle.PasswordResetTokenBucketThrottle]
    
    def post(self, request):
        b_social_auth_service = BSocialAuthService()
        result, error = b_social_auth_service.password_reset(request.data)

        if error:
            return api_error_response_handler.error(
                error=error.get("error"), 
                message=error.get("message"), 
                status_code=error.get("status_code"),
            )

        return api_success_response_handler.success(
                message=result.get("message"), 
                status_code=result.get("status_code"),
                data = result.get("data")
            )
    

class BSocialTokenRefreshView(TokenRefreshView):
    throttle_classes = [throttle.RefreshTokenBucketThrottle]

    serializer_class = BSocialTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        logger.info("Token Refresh starting....")

        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            logger.info("No refresh token found")
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            serializer = self.get_serializer(data={"refresh": refresh_token})
            serializer.is_valid(raise_exception=True)

        except TokenError:
            return api_error_response_handler.error(message="Invalid or expired refresh token", status_code=status.HTTP_400_BAD_REQUEST)

        data = {"access_token": serializer.validated_data.pop("access")}
        logger.info("Access token created")
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # request.auth is a validated SimpleJWT token.
        b_social_auth_service = BSocialAuthService()
        access_token = request.auth
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_401_UNAUTHORIZED)

        result, error = b_social_auth_service.logout(access_token, refresh_token)

        if error:
            return api_error_response_handler.error(message=error["message"], status_code=error["status_code"])
              
        response = api_success_response_handler.success(message=result["message"], status_code=result["status_code"])
        response.delete_cookie("refresh_token")

        return response