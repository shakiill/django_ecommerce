from rest_framework import viewsets, views, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings

from api.cms.serializers import (
    MainSliderSerializer, ContactSerializer, ContactListSerializer, 
    build_mega_menu_structure, SiteSettingSerializer
)
from apps.cms.models import MainSlider, MenuSection, Contact, MEGA_MENU_CACHE_KEY, SiteSetting


class SiteSettingView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        settings = SiteSetting.objects.first()
        serializer = SiteSettingSerializer(settings, context={'request': request})
        return Response(serializer.data)


class MainSliderViewSet(viewsets.ModelViewSet):
    queryset = MainSlider.objects.all()
    serializer_class = MainSliderSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get']
    pagination_class = None


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


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for contact form submissions.
    
    - Public users can POST to submit contact forms
    - Staff users can view all submissions
    """
    queryset = Contact.objects.all()
    pagination_class = None
    
    def get_serializer_class(self):
        if getattr(self, 'action', None) in ['list', 'retrieve']:
            return ContactListSerializer
        return ContactSerializer
    
    def get_permissions(self):
        if getattr(self, 'action', None) == 'create':
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get_authenticators(self):
        if getattr(self, 'action', None) == 'create':
            return []
        return super().get_authenticators()
    
    def create(self, request, *args, **kwargs):
        # Honeypot check
        if request.data.get('website'):
            # Silently ignore if it's a bot (return success to fool them)
            return Response(
                {"message": "Thank you for contacting us! We will get back to you soon."},
                status=status.HTTP_201_CREATED
            )
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Thank you for contacting us! We will get back to you soon."},
            status=status.HTTP_201_CREATED
        )
