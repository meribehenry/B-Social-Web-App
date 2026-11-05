from django.urls import path
from . import views as post_views
from apps.comment.views import CreateCommentView, CreateListCommentDispatcherView


urlpatterns = [
    path("", post_views.CreateListPostDispatcherView.as_view(), name="create-list-posts"),
    path("<uuid:pk>/", post_views.ViewEditDeletePostDispatcherView.as_view(), name="view-patch-delete-post"),
    path("<uuid:pk>/comments/", CreateListCommentDispatcherView().as_view(), name="create-list-comment"),
]