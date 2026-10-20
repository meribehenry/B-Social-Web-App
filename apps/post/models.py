from django.db import models
from django.utils import timezone
from core.model.base_model import BaseModel
from django.utils.text import slugify
from django.conf import settings



class PostTag(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            # making sure it is unique
            while PostTag.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Post(BaseModel):
    title = models.TextField(max_length=200, blank=True, null=True)
    content = models.TextField(max_length=3000, blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now, editable=False)
    date_edited = models.DateTimeField(null=True)
    is_edited = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True, related_name="posts")
    tags = models.ManyToManyField("PostTag", related_name="posts", blank=True)
    batch_id = models.UUIDField(max_length=50, null=True, blank=True)


class PostMedia(BaseModel):
    public_id = models.CharField(max_length=100)
    secure_url = models.URLField(max_length=300)
    format = models.CharField(max_length=10)
    resource_type = models.CharField(max_length=20, choices=[("image", "Image"), ("video", "Video")])
    size = models.IntegerField()
    asset_folder = models.CharField()
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="medias")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_medias")
    upload_session_id = models.UUIDField(max_length=50, null=True, blank=True)