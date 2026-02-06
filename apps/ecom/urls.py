from django.urls import path

from apps.ecom.product import (
    ProductCreateView,
    ProductStep1EditView,
    ProductVariantWarehouseView,
    ProductListView,
    get_attribute_values,
    product_list_ajax,  # <-- Add this import
)
from apps.ecom.product_images import manage_product_images  # added import
from apps.ecom.storefront_views import (
    StorefrontHomeView,
    ProductListView as StorefrontProductListView,
    ProductDetailView,
    CartView,
    CheckoutView,
    CustomerDashboardView,
    OrderHistoryView,
    OrderDetailView,
    AddressManagementView,
    ProfileView,
    ContactView,
)
from apps.user.registration import CustomerRegistrationView, OtpVerificationView

urlpatterns = [
    # Customer-facing storefront
    path('', StorefrontHomeView.as_view(), name='home'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('register/', CustomerRegistrationView.as_view(), name='customer_register'),
    path('register/verify/', OtpVerificationView.as_view(), name='verify_otp'),
    path('shop/', StorefrontProductListView.as_view(), name='shop'),
    path('shop/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Customer dashboard
    path('my-account/', CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('my-account/orders/', OrderHistoryView.as_view(), name='order_history'),
    path('my-account/orders/<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),
    path('my-account/addresses/', AddressManagementView.as_view(), name='addresses'),
    path('my-account/profile/', ProfileView.as_view(), name='profile'),
    
    # Admin product management (keep existing)
    path('product/', ProductListView.as_view(), name='product_list'),
    path('product/ajax/', product_list_ajax, name='product_list_ajax'),  # <-- Add this line
    path('add-product/', ProductCreateView.as_view(), name='product_create'),
    path('product/<int:product_id>/edit-step1/', ProductStep1EditView.as_view(), name='product_step1_edit'),
    path('product/<int:product_id>/variants/', ProductVariantWarehouseView.as_view(), name='product_variants_step'),
    path('ajax/get-attribute-values/', get_attribute_values, name='get_attribute_values'),
    path('product/<int:product_id>/images/', manage_product_images, name='product_images'),  # added path
]
