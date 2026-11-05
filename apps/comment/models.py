from core.model.base_model import BaseModel
from django.db import models
from django.utils import timezone 
from django.conf import settings
from apps.post.service import PostService
from django.contrib.auth import get_user_model

class Comment(BaseModel):
    content = models.CharField(max_length=500)
    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_edited = models.DateTimeField(null=True)
    is_edited = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey("post.Post", on_delete=models.CASCADE, related_name="comments")

