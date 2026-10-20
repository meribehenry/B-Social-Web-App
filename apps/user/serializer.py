from rest_framework import serializers
from .models import User, Profile



class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ["display_name", "profile_pic_url", "following_count", "followers_count"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User

        fields = ["id", "username", "gender", "is_active", "date_joined", "email_verified", "role", "is_staff", "profile"]
        read_only_fields = ["id", "email" , "username", "gender", "is_active", "date_joined", "email_verified", "role", "is_staff", "profile"]


class EditProfileSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=30, required=False, allow_null=True, allow_blank=True, default=None)
    bio = serializers.CharField(max_length=500, required=False, allow_null=True, allow_blank=True, default=None)
    profession = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True, default=None)
    batch_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)


class ProfileUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = ["id", "username", "gender", "is_active", "date_joined", "email_verified", "role", "is_staff"]
        read_only_fields = ["id", "username", "gender", "is_active", "date_joined", "email_verified", "role", "is_staff"]



class ProfileSerializer(serializers.ModelSerializer):
    user = ProfileUserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "display_name", 
            "profile_pic_url", 
            "profile_banner_url", 
            "bio",  
            "profession", 
            "following_count", 
            "followers_count", 
            "posts_count", 
            "comments_count", 
            "replies_count", 
            "like_count", 
            "last_updated", 
            "user"
        ]