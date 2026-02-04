from rest_framework import viewsets, serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import MultiPartParser, FormParser  # <-- add this import

from apps.helpers.utils import IsStaffUser
from apps.master import models as master_models


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Attribute
        fields = '__all__'


class AttributeValueSerializer(serializers.ModelSerializer):
    # Show attribute as object on read, accept id on write
    attribute = serializers.PrimaryKeyRelatedField(
        queryset=master_models.Attribute.objects.all()
    )

    class Meta:
        model = master_models.AttributeValue
        fields = '__all__'


class AttributeViewSet(viewsets.ModelViewSet):
    queryset = master_models.Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class AttributeValueViewSet(viewsets.ModelViewSet):
    queryset = master_models.AttributeValue.objects.select_related('attribute').all()
    serializer_class = AttributeValueSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Brand
        fields = '__all__'

class BrandViewSet(viewsets.ModelViewSet):
    queryset = master_models.Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Tag
        fields = '__all__'

class TagViewSet(viewsets.ModelViewSet):
    queryset = master_models.Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Supplier
        fields = '__all__'

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = master_models.Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Tax
        fields = '__all__'

class TaxViewSet(viewsets.ModelViewSet):
    queryset = master_models.Tax.objects.all()
    serializer_class = TaxSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Unit
        fields = '__all__'

class UnitViewSet(viewsets.ModelViewSet):
    queryset = master_models.Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=master_models.Category.objects.all(),
        many=True,
        required=False
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = master_models.Category
        fields = '__all__'

    def create(self, validated_data):
        parents = validated_data.pop('parent', [])
        category = super().create(validated_data)
        if parents:
            category.parent.set(parents)
        return category

    def update(self, instance, validated_data):
        parents = validated_data.pop('parent', None)
        category = super().update(instance, validated_data)
        if parents is not None:
            category.parent.set(parents)
        return category

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = master_models.Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    parser_classes = [MultiPartParser, FormParser]  # <-- fix here
    pagination_class = None


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Warehouse
        fields = '__all__'

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = master_models.Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Currency
        fields = '__all__'

class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = master_models.Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.PaymentMethod
        fields = '__all__'

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = master_models.PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.ShippingMethod
        fields = '__all__'

class ShippingMethodViewSet(viewsets.ModelViewSet):
    queryset = master_models.ShippingMethod.objects.all()
    serializer_class = ShippingMethodSerializer
    permission_classes = [IsStaffUser]
    authentication_classes = [SessionAuthentication]
    pagination_class = None
