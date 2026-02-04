from rest_framework import serializers

from apps.master import models as master_models


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Brand
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Tag
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Supplier
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Category
        fields = '__all__'


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Warehouse
        fields = '__all__'


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Currency
        fields = '__all__'


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.PaymentMethod
        fields = '__all__'


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.ShippingMethod
        fields = '__all__'


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Tax
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = master_models.Attribute
        fields = '__all__'
