from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = ["id", "email", "name", "username", "gender", "is_active", "date_joined", "email_verified"]
        read_only_fields = ["id", "email", "name", "username", "gender", "is_active", "date_joined", "email_verified"]