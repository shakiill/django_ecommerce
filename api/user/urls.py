from django.urls import path

from api.user import views

urlpatterns = [
    path('customer/register/', views.CustomerRegistrationView.as_view(), name='customer-register'),
    path('otp/verify/', views.OtpVerificationView.as_view(), name='otp-verify'),
    path('login/', views.LoginView.as_view(), name='user_login'),
    path('logout/', views.LogoutView.as_view(), name='user_logout'),
    path('token-validator/', views.TokenValidView.as_view(), name='token-validator'),
    path('profile-update/', views.ProfileUpdateView.as_view(), name='profile-update'),

]
