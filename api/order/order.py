from rest_framework import viewsets, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.order.models import Order, OrderItem, Address, Cart, quantize_money


def _resolve_owner(request, keep_guest=False):
    """
    Resolve (user, guest_token).
    If keep_guest=True and both provided, retain guest_token (used for direct guest-cart checkout after login).
    """
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    guest_token = request.headers.get("X-Guest-Token") or request.query_params.get("guest_token")
    if not user and not guest_token:
        raise serializers.ValidationError({"detail": "guest_token header or query param is required for guest checkout."})
    if user and guest_token and not keep_guest:
        guest_token = None
    return user, guest_token


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "full_name", "email", "phone", "line1", "line2", "city", "state", "postal_code", "country"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()
    product_slug = serializers.SerializerMethodField()
    variant_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product_name", "product_slug", "product_image", "variant_name", "sku", "unit_price", "quantity", "line_total"]

    def get_variant_name(self, obj):
        if obj.variant:
            # Join attribute values like "Red, XL"
            return ", ".join([v.value for v in obj.variant.attributes.all()])
        return ""

    def get_product_image(self, obj):
        if obj.variant and obj.variant.product.images.exists():
            image = obj.variant.product.images.first().image
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.url)
            return image.url
        return None

    def get_product_slug(self, obj):
        if obj.variant:
            return obj.variant.product.slug
        return ""


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    billing_address = AddressSerializer(read_only=True)

    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "status", "payment_status", "currency",
            "subtotal_amount", "discount_amount", "shipping_amount", "tax_amount", "total_amount",
            "coupon_code", "created_at", "items", "items_count", "shipping_address", "billing_address",
            "shipping_method", "shipping_method_name"
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderCreateSerializer(serializers.Serializer):
    guest_email = serializers.EmailField(required=False, allow_null=True, allow_blank=False)
    # Existing full address objects (still required for guests)
    shipping_address = AddressSerializer(required=False)
    billing_address = AddressSerializer(required=False)
    use_shipping_as_billing = serializers.BooleanField(default=True)
    # New: IDs for existing user addresses
    shipping_address_id = serializers.IntegerField(required=False)
    billing_address_id = serializers.IntegerField(required=False)
    shipping_method_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        req = self.context["request"]
        user = req.user if getattr(req.user, "is_authenticated", False) else None
        # Guests must supply guest_email + full shipping_address
        if not user:
            if not attrs.get("guest_email"):
                raise serializers.ValidationError({"guest_email": "guest_email is required for guest checkout."})
            if not attrs.get("shipping_address"):
                raise serializers.ValidationError({"shipping_address": "shipping_address object required for guest checkout."})
        else:
            # User path: must provide either shipping_address_id OR shipping_address object
            if not attrs.get("shipping_address_id") and not attrs.get("shipping_address"):
                raise serializers.ValidationError({"shipping_address": "Provide shipping_address_id or shipping_address object."})
        return attrs


class OrderViewSet(viewsets.ViewSet):
    """
    Order endpoints:
    - GET /orders/ -> list current owner's orders
    - GET /orders/{id}/ -> retrieve order
    - POST /orders/ -> create order from cart with addresses
    """
    permission_classes = [AllowAny]

    def list(self, request):
        user, guest_token = _resolve_owner(request)
        if user:
            qs = Order.objects.filter(user=user)
        else:
            qs = Order.objects.filter(guest_token=guest_token)

        # Filtering logic
        status_filter = request.query_params.get('status')
        date_from = request.query_params.get('created_at__gte')
        date_to = request.query_params.get('created_at__lte')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        qs = qs.select_related('shipping_address', 'billing_address').prefetch_related('items', 'items__variant', 'items__variant__product', 'items__variant__product__images').order_by("-created_at")
        
        # Add pagination support for list view
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginator.page_size_query_param = 'page_size'
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = OrderSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = OrderSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        user, guest_token = _resolve_owner(request)
        qs = Order.objects.all()
        if user:
            order = qs.filter(user=user, pk=pk).first()
        else:
            order = qs.filter(guest_token=guest_token, pk=pk).first()
        if not order:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order, context={'request': request}).data)

    def create(self, request):
        # keep_guest=True so we can optionally use a guest cart while authenticated
        user, guest_token = _resolve_owner(request, keep_guest=True)
        ser = OrderCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        source_guest_token = request.data.get("source_guest_token")
        if user and source_guest_token:
            guest_token = source_guest_token

        # Resolve shipping address
        shipping = None
        if user:
            sid = data.get("shipping_address_id")
            if sid:
                shipping = Address.objects.filter(id=sid, user=user).first()
                if not shipping:
                    raise serializers.ValidationError({"shipping_address_id": "Address not found or not owned by user."})
            else:
                ship_data = data["shipping_address"]
                shipping = Address.objects.create(user=user, **ship_data)
        else:
            # Guest always creates snapshot address (user=None)
            ship_data = data["shipping_address"]
            shipping = Address.objects.create(
                user=None,
                full_name=ship_data["full_name"],
                email=ship_data.get("email") or data.get("guest_email"),
                phone=ship_data.get("phone", ""),
                line1=ship_data["line1"],
                line2=ship_data.get("line2", ""),
                city=ship_data["city"],
                state=ship_data.get("state", ""),
                postal_code=ship_data["postal_code"],
                country=ship_data["country"],
            )

        # Resolve billing
        billing = shipping
        if not data.get("use_shipping_as_billing", True):
            if user:
                bid = data.get("billing_address_id")
                if bid:
                    billing = Address.objects.filter(id=bid, user=user).first()
                    if not billing:
                        raise serializers.ValidationError({"billing_address_id": "Billing address not found or not owned by user."})
                else:
                    bill_data = data.get("billing_address") or data.get("shipping_address")
                    billing = Address.objects.create(user=user, **bill_data)
            else:
                bill_data = data.get("billing_address") or data.get("shipping_address")
                billing = Address.objects.create(
                    user=None,
                    full_name=bill_data["full_name"],
                    email=bill_data.get("email") or data.get("guest_email"),
                    phone=bill_data.get("phone", ""),
                    line1=bill_data["line1"],
                    line2=bill_data.get("line2", ""),
                    city=bill_data["city"],
                    state=bill_data.get("state", ""),
                    postal_code=bill_data["postal_code"],
                    country=bill_data["country"],
                )

        # Select cart
        if user and guest_token:
            cart = Cart.objects.for_owner(guest_token=guest_token)
            if not cart:
                raise serializers.ValidationError({"detail": "Guest cart not found for provided source_guest_token."})
        else:
            cart = Cart.objects.get_or_create_for_owner(user=user, guest_token=guest_token)

        # Resolve shipping method
        from apps.master.models import ShippingMethod
        shipping_method = None
        sm_id = data.get("shipping_method_id")
        if sm_id:
            shipping_method = ShippingMethod.objects.filter(id=sm_id, is_active=True).first()

        order = Order.create_from_cart(
            cart=cart,
            user=user,
            guest_token=guest_token,
            guest_email=data.get("guest_email"),
            shipping_address=shipping,
            billing_address=billing,
            shipping_method=shipping_method,
            currency="BDT",
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
