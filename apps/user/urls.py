from django.urls import path
from .login import UserLoginView, UserLogoutView  # added

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='staff_login'),     # added
    path('logout/', UserLogoutView.as_view(), name='staff_logout'),  # added
]
