from rest_framework import serializers


class MediaInfoSerializer(serializers.Serializer):
    # resource_type = serializers.ChoiceField(choices=["video", "image"])
    extension = serializers.ChoiceField(choices=["png", "img", "mp4", "jpg", "gif", "jpeg", "avif", "mkv"])
    size = serializers.IntegerField()
    purpose = serializers.ChoiceField(choices=["post", "profile_pic", "profile_banner"])

    def validate_size(self, value):
        if value > 104857600:
            raise serializers.ValidationError("Size cannot be more than 100MB")
        return value

    def validate(self, data):
        extension = data.get("extension")
        purpose = data.get("purpose")

        if purpose in {"profile_pic", "profile_banner"} and extension not in  {"png", "img", "jpg", "jpeg"}:
            raise serializers.ValidationError("Profile picture or profile banner must be an image")

        return data
    

class MediaUploadSerializer(serializers.Serializer):
    files_info = MediaInfoSerializer(many=True)