from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth.hashers import make_password
from .services.refresh_token.service import is_refresh_token_revoked
from rest_framework import serializers
from django.contrib.auth import get_user_model
import re


User = get_user_model()

def validate_password(data):
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if len(password) < 8:
        raise serializers.ValidationError({"password": "Password must be at least 8 characters long"})
    
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError({"password": "Password must contain uppercase letter"})
    
    if not re.search(r'[a-z]', password):
        raise serializers.ValidationError({"password": "Password must contain lowercase letter"})

    if not re.search(r'[0-9]', password):
        raise serializers.ValidationError({"password": "Password must contain uppercase letter"})

    if password != confirm_password:
        raise serializers.ValidationError({"confirm_password": "Field does not match password field"})

    return data 

class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=30)
    gender = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()


    def validate_gender(self, value: str): 
        if value.lower() not in ["male", "female"]:
            raise serializers.ValidationError("Gender can only be male or female")
        return value

    def validate_name(self, value):
        if len(value) > 30:
            raise serializers.ValidationError("Name can only be 20 characters long")
        return value

    def validate(self, data):
        return validate_password(data)

class BSocialTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, data):

        refresh = self.token_class(data["refresh"])

        jti = refresh["jti"]

        if is_refresh_token_revoked(jti):
            raise AuthenticationFailed("This refresh token has been revoked.")

        # SimpleJWT now performs its normal refresh flow.
        return super().validate(data)


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.CharField()


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password_reset_token = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        data["password"] = data.pop("new_password")

        return validate_password(data)


