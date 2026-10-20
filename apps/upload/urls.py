from django.urls import path
from . import views as upload_views


urlpatterns = [
    path("", upload_views.UploadMediaFileView.as_view(), name="upload-media-file"),
    path("/", upload_views.UploadMediaFileView.as_view(), name="upload-media-file"),
    path("webhook/callback/", upload_views.WebhookCallbackView.as_view(), name="webhook-callback"),
    path("webhook/callback", upload_views.WebhookCallbackView.as_view(), name="webhook-callback"),
]