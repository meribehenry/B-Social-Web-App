from django.db import models
from core.model.base_model import BaseModel
from django.conf import settings


class UploadBatch(BaseModel):
    class Status(models.TextChoices):
        UPLOADING = "UPLOADING", "Uploading"
        UPLOADED = "UPLOADED", "Uploaded"
        USED = "USED", "Used"
        UNUSED = "UNUSED", "Unused"
        EXPIRED = "EXPIRED", "Expired"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="upload_batches")
    status = models.CharField(max_length=20, choices=Status.choices,default=Status.UPLOADING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)


class UploadSession(BaseModel):
    class Status(models.TextChoices):
        UPLOADING = "UPLOADING", "Uploading"
        UPLOADED = "UPLOADED", "Uploaded"
        USED = "USED", "Used"
        UNUSED = "UNUSED", "Unused"
        EXPIRED = "EXPIRED", "Expired"

    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name="uploads")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=20)
    public_id = models.CharField(max_length=500, unique=True)
    secure_url = models.URLField(null=True,blank=True)
    purpose = models.CharField(max_length=20)
    format = models.CharField(max_length=10)
    bytes = models.IntegerField()
    asset_folder = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)

