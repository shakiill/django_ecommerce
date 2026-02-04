from django.contrib import admin

from apps.user.models import OtpToken, Customer, CustomUser


# Register your models here.

@admin.register(OtpToken)
class OtpTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'attempts', 'used']
    list_filter = ['used']
    search_fields = ['user']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'name', 'is_active', 'is_verified']
    list_filter = ['is_verified', 'is_active']
    search_fields = ['username', 'email', 'name']


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'name', 'is_active', 'is_verified']
    list_filter = ['is_verified', 'is_active']
    search_fields = ['username', 'email', 'name']
