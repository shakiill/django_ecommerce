from rest_framework import viewsets, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.order.models import Order, OrderItem, Address


class TruckingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "title", "full_name", "email", "phone", "line1", "line2", "city", "state", "postal_code",
                  "country"]


class TruckingOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_name", "sku", "unit_price", "quantity", "line_total"]


class TruckingOrderSerializer(serializers.ModelSerializer):
    items = TruckingOrderItemSerializer(many=True, read_only=True)
    shipping_address = TruckingAddressSerializer(read_only=True)
    billing_address = TruckingAddressSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "status", "payment_status", "currency",
            "subtotal_amount", "discount_amount", "shipping_amount", "tax_amount", "total_amount",
            "coupon_code", "created_at", "items", "shipping_address", "billing_address"
        ]


class TruckingOrderViewSet(viewsets.GenericViewSet):
    """
    Public guest-facing trucking/order lookup.
    - GET /order_trucking/?guest_email=foo@bar.com                 -> list guest orders for email
    - GET /order_trucking/?order_id=123&guest_email=foo@bar.com    -> single order by pk or order_number
    - GET /order_trucking/<identifier>/?guest_email=...            -> single order by pk or order_number
    Only guest orders (user_id IS NULL) are exposed and the guest_email must match.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = TruckingOrderSerializer
    queryset = Order.objects.all()
    lookup_field = 'order_number'
    http_method_names = ['get']

    def _get_order_by_identifier(self, identifier):
        """Try integer PK first, then order_number (case-insensitive)."""
        if identifier is None:
            return None
        # try pk
        try:
            pk = int(identifier)
            try:
                return Order.objects.select_related("shipping_address", "billing_address").prefetch_related("items").get(pk=pk)
            except (Order.DoesNotExist, ValueError):
                pass
        except (ValueError, TypeError):
            pass
        # try order_number
        try:
            return Order.objects.select_related("shipping_address", "billing_address").prefetch_related("items") \
                .get(order_number__iexact=str(identifier).strip())
        except Order.DoesNotExist:
            return None

    def _serialize(self, order):
        return self.get_serializer(order).data

    def list(self, request):
        # Accept either guest_email or email
        guest_email = request.query_params.get("guest_email") or request.query_params.get("email")
        # Accept order_id or order_number to return single order via collection endpoint
        order_id_q = request.query_params.get("order_id") or request.query_params.get(self.lookup_field)

        if not guest_email and not order_id_q:
            return Response(
                {"detail": "Provide 'guest_email' (or 'email') to list orders or provide 'order_id'/'order_number' to fetch a single order."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If an identifier was provided on collection, resolve single order
        if order_id_q:
            order = self._get_order_by_identifier(order_id_q)
            if not order:
                return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            # only expose guest orders
            if order.user_id is not None:
                return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            # Only require guest_email match if guest_email was provided
            if guest_email and (order.guest_email or "").strip().lower() != guest_email.strip().lower():
                return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(self._serialize(order), status=status.HTTP_200_OK)

        # List guest orders by email
        if not guest_email:
            return Response({"detail": "Provide 'guest_email' to list orders."}, status=status.HTTP_400_BAD_REQUEST)

        qs = Order.objects.select_related("shipping_address", "billing_address") \
            .prefetch_related("items") \
            .filter(user_id__isnull=True, guest_email__iexact=guest_email.strip()).order_by("-created_at")

        if not qs.exists():
            return Response({"detail": "No orders found for this email."}, status=status.HTTP_404_NOT_FOUND)

        ser = self.get_serializer(qs, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)

    def retrieve(self, request, order_number=None):
        """
        Resolve order by path identifier (pk or order_number).
        guest_email is optional; if provided it must match. Only guest orders are exposed.
        """
        guest_email = request.query_params.get("guest_email") or request.query_params.get("email")

        identifier = order_number
        order = self._get_order_by_identifier(identifier)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.user_id is not None:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        # Only enforce guest_email matching if the client provided an email param
        if guest_email and (order.guest_email or "").strip().lower() != guest_email.strip().lower():
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(self._serialize(order), status=status.HTTP_200_OK)
