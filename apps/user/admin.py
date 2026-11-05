from django.contrib import admin
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_superuser", "is_active", "email_verified", "id", "profile")
    search_fields = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "username", "password", "email_verified", "gender", "status", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_superuser", "email_verified"),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    ordering = ("display_name",)
    list_display = ("display_name", "profile_pic_url", "profile_banner_url", "profession", "user", "bio")
    search_fields = ("display_name",)

