from rest_framework import serializers
from .models import Post, PostMedia, PostTag
from django.contrib.auth import get_user_model
from apps.user.models import Profile


def get_user_model_class():
    return  get_user_model()


class PostAuthorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["profile_pic_url", "display_name"]


class PostAuthorSerializer(serializers.ModelSerializer):
    profile = PostAuthorProfileSerializer(read_only=True)
    class Meta:
        model = get_user_model_class()
        fields = ["id", "username", "profile"]


class PostMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostMedia
        fields = ["id", "resource_type", "secure_url"]
        

class PostTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostTag
        fields = ["id", "name", "slug"]


class PostSerializer(serializers.ModelSerializer):
    medias = PostMediaSerializer(many=True, read_only=True)
    tags = PostTagSerializer(many=True, read_only=True)
    author = PostAuthorSerializer(read_only=True)

    class Meta:
        model = Post
        fields = ["id","title", "content", "date_created", "date_edited", "is_edited", "author", "medias", "tags"]
        read_only_fields = ["id", "title", "content", "date_created", "date_edited", "is_edited", "author"]


class TagsSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class CreatePostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True, default=None)
    content = serializers.CharField(max_length=3000, required=False, allow_null=True, allow_blank=True, default=None)
    batch_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    tags = TagsSerializer(many=True, required=False, allow_null=True, default=[])


class EditPostSerializer(CreatePostSerializer):
    # include_upload_batch = serializers.BooleanField(required=True) 
    # include_tag = serializers.BooleanField(required=True) 
    pass