from core.model.base_model import BaseModel
from django.utils import timezone
from django.conf import settings
from django.db import models



class RevokedAccessToken(BaseModel):
    jti = models.CharField(max_length=255, unique=True, db_index=True,)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="revoked_access_tokens",)
    expires_at = models.DateTimeField(editable=False, db_index=True)
    revoked_at = models.DateTimeField(editable=False,auto_now_add=True)

    def __str__(self):
        return self.jti


class UserToken(BaseModel):
    PURPOSE_CHOICES = [
        ('REGISTRATION', 'Registration Verification'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('CHANGE_PASSWORD', 'Change Password'),
    ]

    # user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="tokens")
    email = models.EmailField()
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
   
    # Store hashes instead of plain text for security
    otp_hash = models.CharField(max_length=64, blank=True, null=True)
    reset_token_hash = models.CharField(max_length=64, blank=True, null=True)
   
    attempts = models.IntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents a user from having multiple active tokens for the same action
        unique_together = ('email', 'purpose')

    def is_expired(self):
        return timezone.now() > self.expires_at

