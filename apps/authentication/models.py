from core.model.base_model import BaseModel
from django.conf import settings
from django.db import models



class RevokedAccessToken(BaseModel):
    jti = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="revoked_access_tokens",
    )

    expires_at = models.DateTimeField(
        editable=False,
        db_index=True,
    )

    revoked_at = models.DateTimeField(
        editable=False,
        auto_now_add=True,
    )

    def __str__(self):
        return self.jti

