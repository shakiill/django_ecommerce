from django.urls import path, include
from rest_framework import routers

from . import views
from .api import (
    AttributeViewSet, AttributeValueViewSet, BrandViewSet, TagViewSet, SupplierViewSet, TaxViewSet,
    UnitViewSet, CategoryViewSet, WarehouseViewSet, CurrencyViewSet, PaymentMethodViewSet, ShippingMethodViewSet
)

# router for API endpoints
router = routers.DefaultRouter()
router.register(r'attributes', AttributeViewSet, basename='attribute')
router.register(r'attribute-values', AttributeValueViewSet, basename='attributevalue')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'taxes', TaxViewSet, basename='tax')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'paymentmethods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'shippingmethods', ShippingMethodViewSet, basename='shippingmethod')

urlpatterns = [
    # page: combined Attributes + Attribute Values
    path('attributes-list/', views.attribute_page, name='attribute_list'),
    # page: combined Brands
    path('brands/', views.brand_page, name='brand_list'),
    # page: combined Tags
    path('tags/', views.tag_page, name='tag_list'),
    # page: combined Suppliers (list)
    path('suppliers/', views.supplier_list, name='supplier_list'),
    # supplier add / edit pages
    path('suppliers/add/', views.supplier_create, name='supplier_add'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    # supplier view (detail JSON for modal)
    path('suppliers/<int:pk>/view/', views.supplier_view, name='supplier_view'),
    # supplier helper API for dynamic form selects
    path('suppliers/api/staff/', views.supplier_staff_list, name='supplier_staff_list'),
    # page: combined Taxes
    path('taxes/', views.tax_page, name='tax_list'),
    # page: combined Units
    path('units/', views.unit_page, name='unit_list'),
    # page: combined Categories
    path('categories/', views.category_page, name='category_list'),
    # page: combined Warehouses
    path('warehouses/', views.warehouse_page, name='warehouse_list'),
    # page: combined Currencies
    path('currencies/', views.currency_page, name='currency_list'),
    # page: combined Payment Methods
    path('payment-methods/', views.paymentmethod_page, name='paymentmethod_list'),
    # page: combined Shipping Methods
    path('shipping-methods/', views.shippingmethod_page, name='shippingmethod_list'),
    # API: /master/api/...
    path('api/', include(router.urls)),
]
