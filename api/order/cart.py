from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.order.models import Cart, CartItem, CartCoupon, Coupon, merge_guest_cart_into_user, quantize_money
from apps.ecom.models import ProductVariant


def _resolve_owner(request):
    """
    Resolves owner as (user_or_none, guest_token_or_none).
    - If authenticated user exists, uses user.
    - Else expects X-Guest-Token header or guest_token query param.
    """
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    guest_token = request.headers.get("X-Guest-Token") or request.query_params.get("guest_token")
    if not user and not guest_token:
        raise serializers.ValidationError({"detail": "guest_token header or query param is required for guest cart."})
    if user and guest_token:
        # Prefer user path; ignore provided guest token to avoid ambiguity
        guest_token = None
    return user, guest_token


class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.IntegerField(source="variant.id", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "variant_id", "sku", "product_name", "product_slug", "quantity", "unit_price", "line_total", "thumbnail"]

    def get_unit_price(self, obj):
        return str(obj.get_unit_price())

    def get_line_total(self, obj):
        return str(obj.line_total)

    def get_thumbnail(self, obj):
        request = self.context.get('request')
        # Try variant image first
        # Note: variant.image (if it exists on model) or lookup via ProductImage logic
        # ProductVariant model usually doesn't have direct image field unless customized, 
        # but let's check if we can access it via attributes logic or if there's a simpler way.
        # Looking at previous serializers, ProductVariantSerializer uses a complex logic to find images.
        # For simplicity/performance in cart, let's just use product thumbnail for now,
        # or check if variant has `image` property.
        # Let's assume fetching the product thumbnail is the safest minimal change.
        # If we really need variant image, we'd need to replicate the query logic.
        
        # Checking ProductVariant model definition would be ideal, but for now fallback to product thumbnail is safe.
        product = obj.variant.product
        if product.thumbnail:
            if request:
                return request.build_absolute_uri(product.thumbnail.url)
            return product.thumbnail.url
        return None


class CartSummarySerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    subtotal = serializers.CharField()
    discount = serializers.CharField()
    shipping = serializers.CharField()
    tax = serializers.CharField()
    total = serializers.CharField()
    coupon = serializers.CharField(allow_blank=True)

    @staticmethod
    def from_cart(cart: Cart):
        items = list(cart.items.select_related("variant", "variant__product"))
        subtotal = sum((i.line_total for i in items), Decimal("0.00"))
        coupon = getattr(cart, "applied_coupon", None)
        discount = Decimal("0.00")
        if coupon:
            discount = coupon.coupon.apply(subtotal)
        shipping = Decimal("0.00")
        tax = Decimal("0.00")
        total = quantize_money(subtotal - discount + shipping + tax)
        return {
            "items": items,
            "subtotal": str(quantize_money(subtotal)),
            "discount": str(quantize_money(discount)),
            "shipping": str(quantize_money(shipping)),
            "tax": str(quantize_money(tax)),
            "total": str(total),
            "coupon": coupon.coupon.code if coupon else "",
        }


class CartAddSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate(self, attrs):
        variant_id = attrs.get("variant_id")
        quantity = attrs.get("quantity")
        variant = get_object_or_404(ProductVariant, pk=variant_id, is_active=True, product__is_active=True)
        attrs["variant"] = variant
        attrs["quantity"] = quantity
        return attrs


class CartUpdateQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class CartViewSet(viewsets.ViewSet):
    """
    Cart endpoints:
    - GET /cart/ -> summary
    - POST /cart/ {variant_id, quantity} -> add or increment item
    - PATCH /cart/items/{id}/ {quantity} -> update line quantity
    - DELETE /cart/items/{id}/ -> remove line
    - POST /cart/apply-coupon/ {code}
    - POST /cart/remove-coupon/
    - POST /cart/clear/
    - POST /cart/merge/ {guest_token} (merge provided guest cart into current user cart)
    """
    permission_classes = [AllowAny]

    def list(self, request):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.get_or_create_for_owner(user=user, guest_token=guest_token)
        data = CartSummarySerializer.from_cart(cart)
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data)

    def create(self, request):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.get_or_create_for_owner(user=user, guest_token=guest_token)
        ser = CartAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        variant = ser.validated_data["variant"]
        qty = ser.validated_data["quantity"]
        try:
            item = cart.items.get(variant=variant)
            item.quantity = item.quantity + qty
            item.save()
        except CartItem.DoesNotExist:
            item = CartItem(cart=cart, variant=variant, quantity=qty)
            item.save()
        data = CartSummarySerializer.from_cart(cart)
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["put", "patch"], url_path=r"items/(?P<pk>[^/.]+)")
    def update_item(self, request, pk=None):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.get_or_create_for_owner(user=user, guest_token=guest_token)
        item = get_object_or_404(CartItem, pk=pk, cart=cart)
        ser = CartUpdateQuantitySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        item.quantity = ser.validated_data["quantity"]
        item.save()
        data = CartSummarySerializer.from_cart(cart)
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data)

    @action(detail=False, methods=["delete"], url_path=r"items/(?P<pk>[^/.]+)")
    def delete_item(self, request, pk=None):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.for_owner(user=user, guest_token=guest_token)
        if not cart:
            return Response(status=status.HTTP_204_NO_CONTENT)
        try:
            item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        item.delete()
        data = CartSummarySerializer.from_cart(cart)
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="apply-coupon")
    def apply_coupon(self, request):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.get_or_create_for_owner(user=user, guest_token=guest_token)
        ser = CouponApplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        code = ser.validated_data["code"]
        ok = CartCoupon.apply(code, cart=cart)
        if not ok:
            return Response({"detail": "Invalid or ineligible coupon."}, status=status.HTTP_400_BAD_REQUEST)
        data = CartSummarySerializer.from_cart(cart)
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data)

    @action(detail=False, methods=["post"], url_path="remove-coupon")
    def remove_coupon(self, request):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.for_owner(user=user, guest_token=guest_token)
        if cart:
            CartCoupon.remove(cart)
        data = CartSummarySerializer.from_cart(cart) if cart else CartSummarySerializer.from_cart(
            Cart.objects.get_or_create_for_owner(user=user, guest_token=guest_token)
        )
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data)

    @action(detail=False, methods=["post"], url_path="clear")
    def clear_cart(self, request):
        user, guest_token = _resolve_owner(request)
        cart = Cart.objects.for_owner(user=user, guest_token=guest_token)
        if cart:
            cart.items.all().delete()
            CartCoupon.remove(cart)
        data = CartSummarySerializer.from_cart(cart) if cart else {"items": [], "subtotal": "0.00", "discount": "0.00",
                                                                   "shipping": "0.00", "tax": "0.00", "total": "0.00",
                                                                   "coupon": ""}
        if "items" in data and isinstance(data["items"], list) and data["items"] and not isinstance(data["items"][0],
                                                                                                    dict):
            data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data)

    @action(detail=False, methods=["post"], url_path="merge")
    def merge_guest(self, request):
        """
        Merge a provided guest cart into the current authenticated user's cart.
        Body: { "guest_token": "<token>" }
        """
        if not getattr(request.user, "is_authenticated", False):
            return Response({"detail": "Authentication required to merge guest cart."},
                            status=status.HTTP_401_UNAUTHORIZED)
        gtok = request.data.get("guest_token") or request.headers.get("X-Guest-Token") or request.query_params.get(
            "guest_token")
        if not gtok:
            return Response({"detail": "guest_token required."}, status=status.HTTP_400_BAD_REQUEST)
        merge_guest_cart_into_user(request.user, gtok)
        cart = Cart.objects.get_or_create_for_owner(user=request.user)
        data = CartSummarySerializer.from_cart(cart)
        data["items"] = CartItemSerializer(data["items"], many=True).data
        return Response(data)
