from django.urls import path
from . import views as comment_views


urlpatterns = [
    path("", comment_views.ViewCommentsView.as_view(), name="list-comment"),
    path("<uuid:pk>/", comment_views.ViewEditDeleteCommentDispatcherView.as_view(), name="view-patch-delete-comment"),
]