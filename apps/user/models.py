from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from uuid6 import uuid7
from django.contrib.auth.hashers import make_password
from core.model.base_model import BaseModel
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, fields):

        email = fields.get("email")

        if not email:
            raise ValueError("Email is required")
        
        fields["email"] = self.normalize_email(email) # Convert everything after the @ to lowercase and standardize the domain
        
        if fields.get("password"):
            fields["password"] = make_password(fields["password"])
            pass
        user = self.model(**fields)

        user.save(using=self._db)
        return user

    def create_superuser(self, **fields):
        fields.setdefault("is_staff", True)
        fields.setdefault("is_superuser", True)
        fields.setdefault("is_active", True)
        fields.setdefault("email_verified", True)

        if fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        
        if fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        
        
        return self.create_user(fields)
    

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid7
    )
    email = models.EmailField(unique=True)
    username = models.CharField(unique=True, null=False)
    gender = models.CharField(max_length=20, choices=[("male", "Male"), ("female", "Female")])
    email_verified = models.BooleanField(default=False)
    has_received_welcome_email = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    status = models.CharField(default="pending_verification")
    role = models.CharField(default="user")
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()


class Profile(BaseModel):
    display_name = models.CharField(max_length=30)
    bio = models.TextField(max_length=500, null=True, blank=True)
    profile_pic_url = models.CharField(max_length=300, null=True, blank=True)
    profile_banner_url = models.CharField(max_length=300, null=True, blank=True)
    profile_pic_public_id = models.CharField(max_length=100, null=True, blank=True)
    profile_banner_public_id = models.CharField(max_length=100, null=True, blank=True)
    profession = models.CharField(max_length=100, null=True, blank=True)
    posts_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    batch_id = models.UUIDField(max_length=50, null=True, blank=True)
    last_updated = models.DateTimeField(null=True)