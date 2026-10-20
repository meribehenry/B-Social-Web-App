from django.urls import  path
from  . import views as user_views

urlpatterns = [
    path("<uuid:pk>", user_views.GetUserView.as_view(), name="get-user"),
    path("<uuid:pk>/", user_views.GetUserView.as_view(), name="get-user"),
    path("<uuid:pk>/profile", user_views.ViewEditProfileDispatcherView.as_view(), name="profile"),
    path("<uuid:pk>/profile/", user_views.ViewEditProfileDispatcherView.as_view(), name="profile"),
]