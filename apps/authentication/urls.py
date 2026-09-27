from django.urls import path
from .views import (
    BSocialTokenRefreshView,
    LogoutView,
    TestView
)


urlpatterns = [
    path(
        "refresh/",
        BSocialTokenRefreshView.as_view(),
        name="token-refresh",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
            "test/",
            TestView.as_view(),
            name="test",
        ),
]
