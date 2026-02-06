from django.urls import path, include, re_path
from rest_framework import routers
from rest_framework.permissions import AllowAny

from api.ecom import views as ecom_views
from api.cms import views as cms_views
from api.master import views as master_views
from api.order.cart import CartViewSet
from api.order.address import AddressViewSet
from api.order.order import OrderViewSet

import os
from django.conf import settings
from django.http import HttpResponse, Http404

from api.order.trucking import TruckingOrderViewSet


def public_api_md(request):
    """
    Serve the api.md file as public Markdown.
    URL: /api/v1/docs/
    """
    try:
        base_dir = getattr(settings, "BASE_DIR", None)
        if not base_dir:
            raise FileNotFoundError("BASE_DIR not set")
        file_path = os.path.join(base_dir, "api.md")
        with open(file_path, "rb") as fh:
            content = fh.read()
    except Exception:
        raise Http404("api.md not found")
    return HttpResponse(content, content_type="text/markdown; charset=utf-8")

# Allow optional trailing slash to avoid Django APPEND_SLASH redirect that breaks PATCH/PUT bodies.
router = routers.DefaultRouter(trailing_slash='/?')
router.APIRootView.permission_classes = [AllowAny]


# Master data endpoints
router.register(r'brands', master_views.BrandViewSet, basename='public_brand')
router.register(r'tags', master_views.TagViewSet, basename='public_tag')
router.register(r'suppliers', master_views.SupplierViewSet, basename='public_supplier')
router.register(r'categories', master_views.CategoryViewSet, basename='public_category')
router.register(r'warehouses', master_views.WarehouseViewSet, basename='public_warehouse')
router.register(r'currencies', master_views.CurrencyViewSet, basename='public_currency')
router.register(r'paymentmethods', master_views.PaymentMethodViewSet, basename='public_paymentmethod')
router.register(r'shippingmethods', master_views.ShippingMethodViewSet, basename='public_shippingmethod')
router.register(r'taxes', master_views.TaxViewSet, basename='public_tax')
router.register(r'attributes', master_views.AttributeViewSet, basename='public_attribute')

router.register(r'products', ecom_views.ProductViewSet, basename='public_product')
router.register(r'popular-products', ecom_views.PopularProductViewSet, basename='public_popular_product')
router.register(r'new-arrival-products', ecom_views.NewArrivalProductViewSet, basename='public_new_arrival_product')

router.register(r'cart', CartViewSet, basename='public_cart')
router.register(r'addresses', AddressViewSet, basename='public_address')
router.register(r'orders', OrderViewSet, basename='public_order')
router.register(r'order_trucking', TruckingOrderViewSet, basename='public_order_trucking')

# API URLs for normal users
router.register(r'public-main-slider', cms_views.MainSliderViewSet, basename='public-main-slider')
router.register(r'contacts', cms_views.ContactViewSet, basename='public_contact')

urlpatterns = [
    # Public docs endpoint (share this link)
    path('docs/', public_api_md, name='public_api_docs'),
    path('mega-menu/', cms_views.MegaMenuView.as_view(), name='public_mega_menu'),
    re_path(
        r'^cart/items/(?P<pk>[^/]+)/?$',
        CartViewSet.as_view({'patch': 'update_item', 'put': 'update_item', 'delete': 'delete_item', 'DELETE': 'delete_item'})
    ),
    path('', include(router.urls)),
    path('', include('api.user.urls')),
]
