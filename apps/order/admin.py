from django.contrib import admin

from apps.order.models import Order


# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'guest_email', 'status', 'payment_status', 'subtotal_amount', 'discount_amount', 'shipping_amount', 'total_amount']
