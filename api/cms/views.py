from rest_framework import viewsets, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings

from api.cms.serializers import MainSliderSerializer, build_mega_menu_structure
from apps.cms.models import MainSlider, MenuSection, MEGA_MENU_CACHE_KEY


class MainSliderViewSet(viewsets.ModelViewSet):
    queryset = MainSlider.objects.all()
    serializer_class = MainSliderSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get']


class MegaMenuView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        if not getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True):
            return Response(self._build_data())
        cached = cache.get(MEGA_MENU_CACHE_KEY)
        if cached is not None:
            return Response(cached)
        data = self._build_data()
        cache.set(MEGA_MENU_CACHE_KEY, data, getattr(settings, 'PUBLIC_API_CACHE_TIMEOUT', 300))
        return Response(data)

    def _build_data(self):
        sections = (
            MenuSection.objects.filter(is_active=True)
            .prefetch_related(
                'groups__items'
            )
            .order_by('order', 'id')
        )
        return build_mega_menu_structure(sections)
