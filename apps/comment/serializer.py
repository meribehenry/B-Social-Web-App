from rest_framework import serializers
from .models import Comment
from django.contrib.auth import get_user_model
from apps.user.models import Profile


def get_user_model_class():
    return  get_user_model()


class CommentAuthorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["profile_pic_url", "display_name"]


class CommentAuthorSerializer(serializers.ModelSerializer):
    profile = CommentAuthorProfileSerializer(read_only=True)
    class Meta:
        model = get_user_model_class()
        fields = ["id", "username", "profile"]


class CommentSerializer(serializers.ModelSerializer):
    author = CommentAuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "date_created", "date_edited", "is_edited", "author"]
        read_only_fields = ["id", "content", "date_created", "date_edited", "is_edited", "author"]


class CreateCommentSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=500)