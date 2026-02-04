from django.urls import path
from . import views

app_name = "order"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("data/", views.order_list_data, name="order_list_data"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
    path("<int:pk>/status/", views.order_status_update, name="order_status_update"),
    path("<int:pk>/invoice/", views.order_invoice, name="order_invoice"),
]
