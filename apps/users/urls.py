from django.urls import path
from .views import (
    UserRegisterView, UserProfileView, AvatarUploadView,
    UserTokenObtainPairView, UserTokenRefreshView,
    PasswordChangeView, AccountDeleteView
)

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="user_register"),
    path("token/", UserTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", UserTokenRefreshView.as_view(), name="token_refresh"),
    path("me/", UserProfileView.as_view(), name="user_profile"),
    path("avatar/", AvatarUploadView.as_view(), name="avatar_upload"),
    path("password/change/", PasswordChangeView.as_view(), name="password_change"),
    path("account/delete/", AccountDeleteView.as_view(), name="account_delete"),
]