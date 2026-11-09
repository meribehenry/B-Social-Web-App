from django.urls import path
from . import views as comment_views


urlpatterns = [
    path("", comment_views.CreateListCommentDispatcherView.as_view(), name="list-create-comments"),
    path("<uuid:pk>/replies/", comment_views.CreateListReplyDispatcherView.as_view(), name="list-create-replies"),
    path("<uuid:pk>/", comment_views.ViewEditDeleteCommentDispatcherView.as_view(), name="view-patch-delete-comment-and-replies"),
]