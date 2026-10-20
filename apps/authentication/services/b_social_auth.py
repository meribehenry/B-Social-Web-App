from datetime import datetime, timezone, timedelta
from django.db import transaction
from django.db.models import F
from core.response import ServiceResponseBuilder
from django.contrib.auth.hashers import make_password
from ..models import  UserToken
from .refresh_token.service import revoke_refresh_token
from .access_token.service import revoke_access_token_object
from django.contrib.auth import get_user_model
from apps.user.serializer import UserSerializer
from ..serializers import LoginSerializer, PasswordResetRequestSerializer, PasswordResetSerializer, RegistrationSerializer, ResendOTPSerializer, VerifyOTPSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from core.logger.logger_client import get_logger
from ..tasks.email_tasks import send_welcome_email, send_otp_email
from apps.user.service import UserService
import secrets
import random
import hashlib


logger = get_logger(__name__)


class BSocialAuthService():

    def __init__(self) -> None:
        self.service_response_builder = ServiceResponseBuilder()
        self.user_service = UserService()
        self.result = {}
        self.error = {}

    def hash_value(self, value: str) -> str:
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def generate_or_update_otp(self, email:str, purpose:str) -> str :
        """ This function generate 6-digit otp and stores it in the database with the email parameter to track users otp"""
        otp_code = random.randint(100000, 999999)

        UserToken.objects.update_or_create(
            email=email, 
            purpose=purpose, 
            defaults={
                'otp_hash': self.hash_value(str(otp_code)),
                'reset_token_hash': None,
                'attempts': 0,
                'expires_at': datetime.now(timezone.utc) + timedelta(minutes=10)
            }
        )
        logger.info(f"OTP generated for {purpose}")
        return str(otp_code)


    def verify_otp(self, email:str, submitted_otp_code:str) -> bool:
        token_record = UserToken.objects.filter(email=email).first()

        if token_record.otp_hash != self.hash_value(submitted_otp_code):
            UserToken.objects.filter(id=token_record.id).update(attempts=F("attempts") + 1, )
            logger.info(f"OTP verification failed for {token_record.purpose}")
            return False
        
        logger.info(f"OTP successfully verified for {token_record.purpose}")
        return True


    def create_username(self, email:str) -> str:
        while True:
            name = email.split("@")[0][:13]
            random = secrets.token_hex(4)
            username = name + "_" + random

            user = self.user_service.get_user_object(identifier=email, retrival_method="username")
            if not user:
                logger.info(f"Username {username} created for {email}")
                return username    


    def register(self, data) -> tuple:
        logger.info("Registration starting....")
        serializer = RegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        email = validated_data.get("email")

        user = self.user_service.get_user_object(identifier=email, retrival_method="email")

        if user and (user.email_verified or user.status == "active"): 
            self.error = self.service_response_builder.conflict_error(
                message =  "Account already exists. Login to continue",
            )
            logger.info("Registeration failed. User already have an active account")
            return self.result, self.error


        if user and user.status == "pending_verification":
            self.error = {
                "message": "Account registered already. Verify your email to continue",
                "error": "Conflict error",
                "data": {"unverified_user": UserSerializer(user).data},
                "status": status.HTTP_409_CONFLICT
            }
            logger.info("Registeration failed. User already registered only verification required")

            return self.result, self.error

        validated_data["username"] = self.create_username(email)
        validated_data["password"] = make_password(validated_data["password"])
        validated_data.pop("confirm_password")

        new_user = self.user_service.create_new_user(validated_data)

        if not new_user:
            self.error = self.service_response_builder.internal_server_error(
                message =  "Could not create account. Please try again",
            )
            logger.info("Could not create account")
            return self.result, self.error

        logger.info("User successfully registered an account. Please verify your email to continue")

        otp = self.generate_or_update_otp(email, "REGISTRATION")
        
        # Send email here
        send_otp_email.delay(email, {"otp":otp})
        # print(otp)

        self.result = self.service_response_builder.result(
            message="An email containing OTP code has been sent. Verify your email to create an account", 
            data= {
                "user": UserSerializer(new_user).data
            },
            status_code=status.HTTP_201_CREATED
        )

        return self.result, self.error


    def OTP_verification(self, data) -> tuple:
        logger.info("OTP verification starting....")
        serializer = VerifyOTPSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        purpose = validated_data.get("purpose")
        otp_code = validated_data.get("otp")

        logger.info(f"Verifying OTP for {purpose}")

        
        user = self.user_service.get_user_object(identifier=email, retrival_method="email")
        token_record = UserToken.objects.filter(email=email, purpose=purpose).first()

        # If OTP or User not found show a genetic message
        if not user or not token_record:
            self.error = self.service_response_builder.bad_request_error(
                message="Invalid request or expired OTP. Please enter a valid email address or request new OTP"
            )
            logger.info("OTP verification failed due to exipred OTP or invalid request")
            return self.result, self.error

        # Brute force protection
        if token_record.attempts >= 3 or token_record.is_expired():
            token_record.delete()
            self.error = self.service_response_builder.bad_request_error(
                message="OTP expired or too many failed attempts or OTP exipired. Request a new one."
            )
            logger.warning("OTP verification failed after three failed attempts")
            return self.result, self.error

        # Verify the OTP
        verdict = self.verify_otp(email, otp_code)
        if verdict is False:
            self.error = self.service_response_builder.validation_error(
                message="Invalid OTP code. Please enter the valid OTP you received"
            )
            logger.info("OTP verification failed due to invalid OTP")
            return self.result, self.error


        if purpose == "REGISTRATION":
            with transaction.atomic():
                self.user_service.mark_user_verified(user)
                token_record.delete()

            logger.info("Account successfully verified")

            User = get_user_model()

            optimised_user = User.objects.defer(
                "has_received_welcome_email"
                ).select_related("profile").get(pk=user.id)

            # Send welcome email here
            send_welcome_email.delay(email)

            # Create access and refresh token
            refresh = RefreshToken.for_user(optimised_user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            logger.info("Access and Refresh token created")

            self.result = self.service_response_builder.result(
                message="Account verification completed", 
                data= {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": UserSerializer(optimised_user).data
                }
            )
        
        elif purpose == 'PASSWORD_RESET':
            # Generate temporary reset token handshake
            raw_password_reset_token = secrets.token_hex(32)
           
            # Upgrade the record: Remove OTP, insert Reset Token, extend expiry
            token_record.otp_hash = None
            token_record.reset_token_hash = self.hash_value(raw_password_reset_token)
            token_record.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
            token_record.attempts = 0
            token_record.save()
            logger.info("Reset token created successfully for PASSWORD_RESET")

            # Pass the raw reset token back securely to the frontend state
            self.result = self.service_response_builder.result(
                data= {
                    "reset_token": raw_password_reset_token
                }
            )
        
        return self.result, self.error


    def resend_OTP(self, data):
        logger.info(f"Resending OTP starting....")
        serializer = ResendOTPSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        purpose = validated_data.get("purpose")

        logger.info(f"Resending OTP for {purpose}")

        user = self.user_service.get_user_object(identifier=email, retrival_method="email")


        if purpose == "REGISTRATION" and user and user.email_verified:
            self.error = self.service_response_builder.conflict_error(
                message =  "Account already exists. Login to continue",
            )
            logger.info("Resending OTP failed for REGISTRATION. User already have an active account")
            return self.result, self.error

        if purpose == "PASSWORD_RESET" and user and not user.email_verified:
            self.error = self.service_response_builder.bad_request_error(
                message =  "Invalid request. Please complete your account creation",
            )
            logger.info("Resending OTP failed for PASSWORD_RESET. User don't have an active account")
            return self.result, self.error


        if user:
            otp = self.generate_or_update_otp(email, purpose)
            send_otp_email.delay(email, {"otp":otp})
            # print(otp)
            logger.info("OTP Resent")

        self.result = self.service_response_builder.result(
            message =  "An email containing the OTP code has been sent",
            status_code=status.HTTP_200_OK
        )

        return self.result, self.error


    def login(self, data):
        logger.info("Logging in starting....")
        serializer = LoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        password = validated_data.get("password")

        user = self.user_service.get_user_object(identifier=email, retrival_method="email")


        if user and not user.email_verified:
            self.error = {
                "message": "Account registered but needs verification. Verify your email to continue",
                "error": "Unauthorized error",
                "data": {"unverified_user": UserSerializer(data=user)},
                "status": status.HTTP_401_UNAUTHORIZED
            }
            logger.info("Login failed due to unverified account")

            return self.result, self.error

        if not user or not user.check_password(password):
            self.error = self.service_response_builder.unauthenticated_error(
                message = "Invalid credentials. Please enter a correct email and password",
            )
            logger.info("Login failed due to invalid credentials")
            return self.result, self.error

        logger.info("Login successful")

        User = get_user_model()

        optimised_user = User.objects.defer(
                        "has_received_welcome_email"
                        ).select_related("profile").get(pk=user.id)

        refresh = RefreshToken.for_user(optimised_user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        logger.info("Access and Refresh token created")

        self.result = self.service_response_builder.result(
            message="Successfully logged in",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": UserSerializer(optimised_user).data
            },
            status_code=status.HTTP_200_OK
        )

        return self.result, self.error
    

    def password_reset_request(self, data):
        logger.info("Password Reset Request starting....")
        serializer = PasswordResetRequestSerializer(data=data) 
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        email = validated_data.get("email")
        purpose = "PASSWORD_RESET"

        user = self.user_service.get_user_object(identifier=email, retrival_method="email")


        if user and not user.email_verified: 
            self.error = self.service_response_builder.bad_request_error(
                message =  "Invalid request. Please complete your account creation",
            )
            logger.info("Password reset request failed. User don't have an active account")
            return self.result, self.error

        if user and user.email_verified:
            otp = self.generate_or_update_otp(email, purpose)
            send_otp_email.delay(email, {"otp":otp})
            print(otp)

        self.result = self.service_response_builder.result(
            message =  "An email containing the OTP code has been sent",
            status_code=status.HTTP_200_OK
        )

        return self.result, self.error

    def password_reset(self, data):
        logger.info("Password Reset starting....")
        serializer = PasswordResetSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        email = validated_data.get("email")
        password = validated_data.get("password")
        password_reset_token = validated_data.get("password_reset_token")

        user = self.user_service.get_user_object(identifier=email, retrival_method="email")
        token_record = UserToken.objects.filter(email=email, purpose='PASSWORD_RESET').first()

        if not user or not token_record:
            self.error = self.service_response_builder.bad_request_error(
                message="Invalid request. Please check your inputs or request a new password reset"
            )
            logger.info("Password reset failed due to invalid request. Either user not found or token_record not found")
            return self.result, self.error

        if token_record.is_expired() or token_record.reset_token_hash != self.hash_value(password_reset_token):
            token_record.delete()
            self.error = self.service_response_builder.validation_error(
                message="Invalid or expired reset token. Please send a new password reset request"
            )
            logger.info("Password reset failed due to invalid or expired reset token")
            return self.result, self.error

        with transaction.atomic():
            # Update user's password securely
            self.user_service.change_password(user, make_password(password))
        
            # Completely remove token record after usage
            token_record.delete()
            logger.info("Password successfully resetted")

            self.result = self.service_response_builder.result(
                message =  "Password reset successfully. You can now login",
                status_code=status.HTTP_200_OK
            )

            return self.result, self.error
        
        self.error = self.service_response_builder.internal_server_error(
            message="An error occured. Please try again"
        )
        logger.error("DB error. Could not change user password")
        return self.result, self.error


    def logout(self, access_token, refresh_token):
        logger.info("Logging out starting....")
        
        # Revoke current access token.
        if access_token:
            revoke_access_token_object(access_token)

        # Revoke refresh token.
        if refresh_token:
            revoke_refresh_token(refresh_token)

        self.result = self.service_response_builder.result(message="Successfully logged out")
        logger.info("Successfully logged out")

        return self.result, self.error