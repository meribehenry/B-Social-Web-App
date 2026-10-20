from django.urls import path
from . import views as post_views


urlpatterns = [
    path("", post_views.CreateListPostDispatcherView.as_view(), name="create-list-posts"),
    path("<uuid:pk>", post_views.ViewEditDeletePostDispatcherView.as_view(), name="view-patch-delete-post"),
    path("<uuid:pk>/", post_views.ViewEditDeletePostDispatcherView.as_view(), name="view-patch-delete-post"),
]