from django.contrib import admin
from .models import UploadSession, UploadBatch


admin.site.register(UploadBatch)
admin.site.register(UploadSession)
