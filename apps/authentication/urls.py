from django.urls import path
from . import views as auth_views


urlpatterns = [
    path("register/", auth_views.RegristrationView.as_view(), name="register"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("verify-otp/", auth_views.VerifyOTPView.as_view(), name="otp-verification"),
    path("password-reset-request/", auth_views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password-reset"),
    path("resend-otp/", auth_views.ResendOTPView.as_view(), name="resend-otp"),
    path("refresh/", auth_views.BSocialTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout",),
    path("test/", auth_views.TestView.as_view(), name="test" ),

    # NO SLASH
    path("register", auth_views.RegristrationView.as_view(), name="register"),
    path("login", auth_views.LoginView.as_view(), name="login"),
    path("verify-otp", auth_views.VerifyOTPView.as_view(), name="verify-otp"),
    path("password-reset-request", auth_views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset", auth_views.PasswordResetView.as_view(), name="password-reset"),
    path("resend-otp", auth_views.ResendOTPView.as_view(), name="resend-otp"),
    path("refresh", auth_views.BSocialTokenRefreshView.as_view(), name="token-refresh"),
    path("logout", auth_views.LogoutView.as_view(), name="logout",),
    path("test", auth_views.TestView.as_view(), name="test" ),
]
