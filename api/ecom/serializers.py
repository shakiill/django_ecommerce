from rest_framework import serializers

from apps.ecom.models import Product, ProductImage, ProductVariant, Wishlist


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'display_order', 'attributes']


class ProductVariantSerializer(serializers.ModelSerializer):
    image_list = serializers.SerializerMethodField()
    is_default = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ['id', 'is_default', 'price', 'discount_price', 'is_discount', 'attributes', 'image_list']

    def get_is_default(self, obj):
        return obj.product.default_variant_id == obj.id

    def get_image_list(self, obj):
        request = self.context.get('request')
        at_values = obj.attributes.all()

        # Filter product images that match ANY of the variant's attributes
        images = ProductImage.objects.filter(
            product=obj.product,
            attributes__in=at_values
        ).distinct()

        return [
            request.build_absolute_uri(image.image.url)
            for image in images
        ] if request else [img.image.url for img in images]

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    old_price = serializers.SerializerMethodField()
    on_sale = serializers.SerializerMethodField()
    thumbnail = serializers.ImageField(read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    is_in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'category', 'category_name', 'brand', 'brand_name',
            'product_type', 'is_featured', 'thumbnail', 'thumbnail_hover', 'unit', 'unit_name', 'price',
            'old_price', 'on_sale', 'default_variant', 'is_active', 'is_in_wishlist'
        ]

    def get_is_in_wishlist(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if product is in user's wishlist
            # Note: For high traffic, consider prefetching or annotation in ViewSet
            from apps.ecom.models import Wishlist
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False

    def get_price(self, obj):
        if obj.default_variant and obj.default_variant.is_on_sale:
            return obj.default_variant.discount_price
        return obj.get_price()

    def get_old_price(self, obj):
        if obj.default_variant and obj.default_variant.is_on_sale:
            return obj.default_variant.price
        return None

    def get_on_sale(self, obj):
        return obj.default_variant.is_on_sale if obj.default_variant else False

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None


class ProductDetailsSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    thumbnail = serializers.ImageField(read_only=True)
    thumbnail_hover = serializers.ImageField(read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)

    attributes_list = serializers.SerializerMethodField()

    variant_list = serializers.SerializerMethodField()
    
    is_in_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Product
        exclude = ['created_at', 'updated_at', 'profit_margin', 'track_inventory', 'allow_backorder',
                   'max_order_quantity', 'created_by', 'updated_by']

    def get_price(self, obj):
        return obj.get_price()

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None

    def get_is_in_wishlist(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if product is in user's wishlist
            from apps.ecom.models import Wishlist
            return Wishlist.objects.filter(user=request.user, product=obj).exists()
        return False

    def get_attributes_list(self, obj):
        # Gather all attribute values used by this product's variants
        variants = obj.variants.prefetch_related('attributes__attribute')
        attr_map = {}
        for variant in variants:
            for attr_value in variant.attributes.all():
                attr = attr_value.attribute
                if attr.id not in attr_map:
                    attr_map[attr.id] = {
                        "name": attr.name,
                        "id": attr.id,
                        "values": {}
                    }
                # Use value id as key to avoid duplicates
                attr_map[attr.id]["values"][attr_value.id] = {
                    "id": attr_value.id,
                    "value": attr_value.value,
                    "color_code": attr_value.color_code
                }
        # Format as list for frontend
        result = []
        for attr in attr_map.values():
            result.append({
                "name": attr["name"],
                "id": attr["id"],
                "values": list(attr["values"].values())
            })
        return result

    def get_variant_list(self, obj):
        variants = ProductVariant.objects.filter(product=obj).prefetch_related('attributes')
        data = ProductVariantSerializer(variants, many=True, context=self.context).data
        return data


class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'product_details', 'created_at']
        extra_kwargs = {
            'user': {'read_only': True},
            'product': {'required': True},
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)
        return wishlist_item

