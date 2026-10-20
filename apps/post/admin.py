from django.contrib import admin
from .models import Post, PostMedia, PostTag


admin.site.register(Post)
admin.site.register(PostMedia)
@admin.register(PostTag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}