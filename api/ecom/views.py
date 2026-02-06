from django.conf import settings
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from api.ecom.new_arrival import NewProductSerializer
from api.ecom.serializers import ProductListSerializer, ProductDetailsSerializer, WishlistSerializer
from apps.ecom.models import Product, Wishlist
from apps.master.models import Category, Brand


# Helper to generate stable cache keys for list/retrieve
def _build_cache_key(prefix: str, request, extra: str = '') -> str:
    params = request.GET.dict()
    if params:
        # Sort params for stable ordering
        serialized = '&'.join(f"{k}={params[k]}" for k in sorted(params.keys()))
    else:
        serialized = ''
    return f"public:{prefix}:{extra}:{serialized}" if serialized else f"public:{prefix}:{extra}"  # no trailing colon if empty


# Cached mixin behavior for read-only endpoints
class CachedReadOnlyMixin:
    cache_timeout = getattr(settings, 'PUBLIC_API_CACHE_TIMEOUT', 300)

    def list(self, request, *args, **kwargs):
        if not getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True):
            return super().list(request, *args, **kwargs)
        
        # Bypass cache for authenticated users to show personalized data (e.g. wishlist status)
        if request.user.is_authenticated:
            return super().list(request, *args, **kwargs)

        key = _build_cache_key(self.__class__.__name__, request, 'list')
        data = cache.get(key)
        if data is None:
            response = super().list(request, *args, **kwargs)
            cache.set(key, response.data, self.cache_timeout)
            return response
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        if not getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True):
            return super().retrieve(request, *args, **kwargs)
            
        # Bypass cache for authenticated users
        if request.user.is_authenticated:
            return super().retrieve(request, *args, **kwargs)

        # Include object identifier and attributes param variations
        obj_id = kwargs.get(self.lookup_field, '') or kwargs.get('pk', '')
        key = _build_cache_key(self.__class__.__name__, request, f"retrieve:{obj_id}")
        data = cache.get(key)
        if data is None:
            response = super().retrieve(request, *args, **kwargs)
            cache.set(key, response.data, self.cache_timeout)
            return response
        return Response(data)


import django_filters


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="default_variant__price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="default_variant__price", lookup_expr='lte')
    category = django_filters.ModelMultipleChoiceFilter(queryset=Category.objects.all())
    brand = django_filters.ModelMultipleChoiceFilter(queryset=Brand.objects.all())

    class Meta:
        model = Product
        fields = ['is_active', 'is_featured', 'category', 'brand', 'product_type', 'unit']


class ProductViewSet(CachedReadOnlyMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    permission_classes = [AllowAny]
    # authentication_classes = []  # Removed to allow request.user to be populated
    http_method_names = ['get']
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'short_description', 'description']
    filterset_class = ProductFilter
    ordering_fields = [
        'id', 'name', 'created_at', 'is_active', 'is_featured', 'default_variant__price'
    ]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailsSerializer
        return ProductListSerializer

    def retrieve(self, request, *args, **kwargs):
        # Override custom retrieve logic but keep caching wrapper executed above by calling parent if cache miss
        if not getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True) or request.user.is_authenticated:
            return super().retrieve(request, *args, **kwargs)
        obj_id = kwargs.get(self.lookup_field, '') or kwargs.get('pk', '')
        key = _build_cache_key(self.__class__.__name__, request, f"retrieve:{obj_id}")
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        instance = self.get_object()
        attributes_param = request.query_params.get('attributes')
        variant = None

        if attributes_param:
            attr_ids = [int(i) for i in attributes_param.split(',') if i.isdigit()]
            if attr_ids:
                # Find a variant that has exactly these attribute values
                variants = instance.variants.all()
                for v in variants:
                    v_attr_ids = set(v.attributes.values_list('id', flat=True))
                    if set(attr_ids) == v_attr_ids:
                        variant = v
                        break

        serializer = self.get_serializer(instance)
        data = serializer.data

        # If a matching variant is found, override price, thumbnail, and default_variant
        if variant:
            data['price'] = str(variant.price)
            if variant.image:
                data['thumbnail'] = request.build_absolute_uri(variant.image.url)
            else:
                if instance.thumbnail:
                    data['thumbnail'] = request.build_absolute_uri(instance.thumbnail.url)
                else:
                    data['thumbnail'] = None
            data['default_variant'] = variant.id
        else:
            # fallback to product's default_variant
            data['default_variant'] = instance.default_variant.id if instance.default_variant else None

        cache.set(key, data, getattr(settings, 'PUBLIC_API_CACHE_TIMEOUT', 300))
        return Response(data)


class PopularProductViewSet(CachedReadOnlyMixin, viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get']
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'short_description', 'description']
    filterset_fields = [
        'is_active', 'is_featured', 'category', 'brand', 'product_type', 'unit'
    ]
    ordering_fields = [
        'id', 'name', 'created_at', 'is_active', 'is_featured'
    ]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(is_active=True).order_by('-id')[:8]


class NewArrivalProductViewSet(CachedReadOnlyMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = NewProductSerializer
    permission_classes = [AllowAny]
    # authentication_classes = []
    http_method_names = ['get']
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'short_description', 'description']
    filterset_fields = []

    def get_queryset(self):
        return Product.objects.filter(is_active=True, is_featured=True).order_by('-created_at')


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='check/(?P<product_id>[^/]+)')
    def check_product(self, request, product_id=None):
        """Check if a product is in the user's wishlist."""
        exists = Wishlist.objects.filter(user=request.user, product_id=product_id).exists()
        return Response({'is_in_wishlist': exists})
    
    @action(detail=False, methods=['post'], url_path='remove_by_product')
    def remove_by_product(self, request):
        """Remove item from wishlist using product_id."""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'Product ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted, _ = Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
        if deleted:
            return Response({'status': 'removed'}, status=status.HTTP_200_OK)
        return Response({'error': 'Not found in wishlist'}, status=status.HTTP_404_NOT_FOUND)

