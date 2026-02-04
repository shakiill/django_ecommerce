from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.order.models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "title", "full_name", "email", "phone", "line1", "line2", "city", "state", "postal_code", "country"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Address.objects.create(user=user, **validated_data)

class AddressViewSet(viewsets.ModelViewSet):
    """
    Endpoints:
    - GET /addresses/ -> list user's addresses
    - GET /addresses/{id}/ -> retrieve one
    - POST /addresses/ -> create new address
    - PUT /addresses/{id}/ -> full update
    - PATCH /addresses/{id}/ -> partial update
    - DELETE /addresses/{id}/ -> delete address
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by("-id")

    def update(self, request, *args, **kwargs):
        # Full update (PUT)
        instance = self.get_object()
        ser = self.get_serializer(instance, data=request.data, partial=False)
        ser.is_valid(raise_exception=True)
        ser.save()  # user unchanged
        return Response(ser.data)

    def partial_update(self, request, *args, **kwargs):
        # Partial update (PATCH)
        instance = self.get_object()
        ser = self.get_serializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
