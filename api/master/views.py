from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response

from api.master import serializers as master_serializers
from apps.master import models as master_models


# Reusable cache key builder

def _m_build_cache_key(prefix: str, request, extra: str = '') -> str:
    params = request.GET.dict()
    if params:
        serialized = '&'.join(f"{k}={params[k]}" for k in sorted(params.keys()))
    else:
        serialized = ''
    return f"public:master:{prefix}:{extra}:{serialized}" if serialized else f"public:master:{prefix}:{extra}"


class MasterCachedMixin:
    cache_timeout = getattr(settings, 'PUBLIC_API_CACHE_TIMEOUT', 300)

    def list(self, request, *args, **kwargs):
        if not getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True):
            return super().list(request, *args, **kwargs)
        key = _m_build_cache_key(self.__class__.__name__, request, 'list')
        data = cache.get(key)
        if data is None:
            response = super().list(request, *args, **kwargs)
            cache.set(key, response.data, self.cache_timeout)
            return response
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        if not getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True):
            return super().retrieve(request, *args, **kwargs)
        obj_id = kwargs.get(getattr(self, 'lookup_field', 'pk'), '') or kwargs.get('pk', '')
        key = _m_build_cache_key(self.__class__.__name__, request, f"retrieve:{obj_id}")
        data = cache.get(key)
        if data is None:
            response = super().retrieve(request, *args, **kwargs)
            cache.set(key, response.data, self.cache_timeout)
            return response
        return Response(data)


class BrandViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Brand.objects.all()
    serializer_class = master_serializers.BrandSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'is_active']
    pagination_class = None


class TagViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Tag.objects.all()
    serializer_class = master_serializers.TagSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'is_active']
    pagination_class = None


class SupplierViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Supplier.objects.all()
    serializer_class = master_serializers.SupplierSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'phone']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'email', 'phone', 'is_active']
    pagination_class = None


class CategoryViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Category.objects.all()
    serializer_class = master_serializers.CategorySerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active', 'is_featured', 'parent']
    ordering_fields = ['id', 'name', 'is_active',  'is_featured', 'parent']
    pagination_class = None


class WarehouseViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Warehouse.objects.all()
    serializer_class = master_serializers.WarehouseSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'location', 'is_active']
    pagination_class = None


class CurrencyViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Currency.objects.all()
    serializer_class = master_serializers.CurrencySerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'symbol']
    filterset_fields = ['is_active']
    ordering_fields = ['id',  'code', 'symbol', 'is_active']
    pagination_class = None


class PaymentMethodViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.PaymentMethod.objects.all()
    serializer_class = master_serializers.PaymentMethodSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'is_active']
    pagination_class = None


class ShippingMethodViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.ShippingMethod.objects.all()
    serializer_class = master_serializers.ShippingMethodSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'is_active']
    pagination_class = None


class TaxViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Tax.objects.all()
    serializer_class = master_serializers.TaxSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'rate', 'is_active']
    pagination_class = None


class AttributeViewSet(MasterCachedMixin, viewsets.ModelViewSet):
    queryset = master_models.Attribute.objects.all()
    serializer_class = master_serializers.AttributeSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get', ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    filterset_fields = ['is_active']
    ordering_fields = ['id', 'name', 'is_active']
    pagination_class = None
