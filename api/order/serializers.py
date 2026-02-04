from rest_framework import serializers

from apps.order.models import Cart


class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    variant_id = serializers.IntegerField(source='variant.id', read_only=True)
    thumbnail = serializers.ImageField(source='variant.product.thumbnail', read_only=True)
    price = serializers.DecimalField(source='variant.price', max_digits=10, decimal_places=2, read_only=True)
    is_discounted = serializers.BooleanField(source='variant.is_discounted', read_only=True)
    discounted_price = serializers.DecimalField(source='variant.discounted_price', max_digits=10, decimal_places=2,
                                                read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'variant_id', 'product_name', 'quantity', 'added_at',
            'thumbnail', 'price', 'is_discounted', 'discounted_price'
        ]
