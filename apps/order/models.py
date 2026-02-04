import uuid
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django.utils import timezone

from apps.user.models import CustomUser

# Money helper
TWO_PLACES = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return (value or Decimal("0.00")).quantize(TWO_PLACES)


# Enums
class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PaymentMethod(models.TextChoices):
    COD = "cod", "Cash on Delivery"
    SSL_COMMERZ = "ssl_commerz", "SSL Commerz"
    PAYSTATION = "paystation", "Pay Station"


# ---- Cart / Cart Manager ----
class CartManager(models.Manager):
    """Helpers to fetch/create a cart and compute totals for a user's or guest's cart."""

    def for_owner(self, user: Optional[CustomUser] = None, guest_token: Optional[str] = None):
        """
        Returns the Cart instance for the owner (either user or guest_token) or None.
        Enforces XOR semantics.
        """
        if user and guest_token:
            raise ValueError("Provide either user or guest_token, not both.")
        if not user and not guest_token:
            raise ValueError("Either user or guest_token must be provided.")
        qs = self.get_queryset()
        return qs.filter(user=user).first() if user else qs.filter(guest_token=guest_token).first()

    def get_or_create_for_owner(self, user: Optional[CustomUser] = None, guest_token: Optional[str] = None):
        """Return a Cart instance, creating if necessary."""
        if user and guest_token:
            raise ValueError("Provide either user or guest_token, not both.")
        if not user and not guest_token:
            raise ValueError("Either user or guest_token must be provided.")
        if user:
            cart, _ = self.get_or_create(user=user, guest_token=None)
        else:
            cart, _ = self.get_or_create(user=None, guest_token=guest_token)
        return cart

    def subtotal(self, user: Optional[CustomUser] = None, guest_token: Optional[str] = None) -> Decimal:
        cart = self.for_owner(user=user, guest_token=guest_token)
        if not cart:
            return Decimal("0.00")
        return cart.subtotal()

    def total_quantity(self, user: Optional[CustomUser] = None, guest_token: Optional[str] = None) -> int:
        cart = self.for_owner(user=user, guest_token=guest_token)
        return cart.total_quantity() if cart else 0

    def owner_filter(self, user: Optional[CustomUser] = None, guest_token: Optional[str] = None):
        """Return a Q object you can use to filter by owner."""
        if user and guest_token:
            raise ValueError("Provide either user or guest_token, not both.")
        if user:
            return Q(user=user)
        return Q(guest_token=guest_token)


class Cart(models.Model):
    """Cart container for either an authenticated user or a guest (via guest_token)."""
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="carts", null=True, blank=True
    )
    guest_token = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CartManager()

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["guest_token"]),
        ]
        constraints = [
            # Exactly one owner (user XOR guest_token)
            models.CheckConstraint(
                name="cart_owner_xor",
                check=(
                    (Q(user__isnull=False) & Q(guest_token__isnull=True)) |
                    (Q(user__isnull=True) & Q(guest_token__isnull=False))
                ),
            ),
            # One cart per user
            models.UniqueConstraint(
                fields=["user"], name="uniq_cart_per_user", condition=Q(user__isnull=False)
            ),
            # One cart per guest token
            models.UniqueConstraint(
                fields=["guest_token"], name="uniq_cart_per_guest", condition=Q(guest_token__isnull=False)
            ),
        ]
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def __str__(self):
        owner = self.user.email if self.user else f"guest:{self.guest_token}"
        return f"Cart({owner})"

    # Aggregates
    def subtotal(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.select_related("variant", "variant__product"):
            total += quantize_money(item.line_total)
        return quantize_money(total)

    def total_quantity(self) -> int:
        agg = self.items.aggregate(total_qty=Sum("quantity"))
        return int(agg["total_qty"] or 0)

    def item_count(self) -> int:
        return self.items.count()

    @property
    def is_guest(self) -> bool:
        return self.user_id is None

    @property
    def owner_type(self) -> str:
        return "guest" if self.is_guest else "user"

    @property
    def owner_identifier(self) -> str:
        """Returns user id (as str) or guest_token for logging/tracking."""
        return str(self.user_id) if not self.is_guest else self.guest_token

    @property
    def owner_email(self) -> Optional[str]:
        return self.user.email if self.user_id else None


class CartItem(models.Model):
    """Cart line item."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "ecom.ProductVariant", on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-added_at",)
        indexes = [
            models.Index(fields=["cart"]),
            models.Index(fields=["variant"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"], name="uniq_variant_per_cart"
            ),
            models.CheckConstraint(
                name="cartitem_qty_gte_1", check=Q(quantity__gte=1)
            ),
        ]
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        owner = self.cart.user.email if self.cart.user else f"guest:{self.cart.guest_token}"
        return f"{owner} - {self.variant.sku} x {self.quantity}"

    def get_unit_price(self) -> Decimal:
        """Effective unit price considering variant discounts. Uses variant method if available."""
        # Prefer a method on variant to centralize logic
        if hasattr(self.variant, "get_effective_price"):
            return quantize_money(self.variant.get_effective_price())
        # Fallback to attributes used in previous models
        if getattr(self.variant, "is_on_sale", False) and getattr(self.variant, "discount_price", None) is not None:
            return quantize_money(self.variant.discount_price)
        return quantize_money(self.variant.price)

    @property
    def line_total(self) -> Decimal:
        return quantize_money(self.get_unit_price() * self.quantity)

    def clean(self):
        if self.quantity < 1:
            raise ValidationError("Quantity must be >= 1.")
        # Enforce product min/max safely (use defaults if missing)
        if self.variant and getattr(self.variant, "product", None):
            p = self.variant.product
            min_q = getattr(p, "min_order_quantity", 1) or 1
            max_q = getattr(p, "max_order_quantity", 100) or 100
            if self.quantity < min_q:
                raise ValidationError(f"Minimum order quantity is {min_q}.")
            if self.quantity > max_q:
                raise ValidationError(f"Maximum order quantity is {max_q}.")
        # Stock checks (use variant.stock if present) - respect allow_backorder
        if self.variant:
            variant_stock = getattr(self.variant, "stock", None)
            allow_backorder = getattr(self.variant.product, "allow_backorder", False)
            if variant_stock is not None and not allow_backorder:
                # previous bug: compared to literal 15000; use actual variant.stock
                if self.quantity > variant_stock:
                    raise ValidationError("Requested quantity exceeds available stock.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


# Updated utility: merge guest cart into user's cart (container + items)
def merge_guest_cart_into_user(user: CustomUser, guest_token: str):
    """
    Merge a guest cart into the user's cart (summing quantities and respecting constraints).
    Use when a guest signs in (claiming their guest cart).
    """
    if not guest_token:
        return
    with transaction.atomic():
        guest_cart = Cart.objects.for_owner(guest_token=guest_token)
        if not guest_cart:
            return
        user_cart = Cart.objects.get_or_create_for_owner(user=user)

        # Merge items (sum quantities)
        for gi in guest_cart.items.select_related("variant"):
            try:
                existing = user_cart.items.get(variant=gi.variant)
                existing.quantity = existing.quantity + gi.quantity
                existing.save()
            except CartItem.DoesNotExist:
                gi.cart = user_cart
                gi.save()

        # Move coupon if any and none on user_cart
        guest_cc = getattr(guest_cart, "applied_coupon", None)
        user_cc = getattr(user_cart, "applied_coupon", None)
        if guest_cc and not user_cc:
            # Transfer only if still valid on user's resulting subtotal
            if guest_cc.coupon.is_valid(user_cart.subtotal()):
                guest_cc.cart = user_cart
                guest_cc.save(update_fields=["cart"])
            else:
                guest_cc.delete()

        # Remove empty guest cart container (items already moved)
        # If you prefer to keep guest_cart for analytics, skip delete()
        guest_cart.delete()


# ---- Address ----
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="addresses")
    title = models.CharField(max_length=50, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=2)  # ISO 3166-1 alpha-2
    created_at = models.DateTimeField(auto_now_add=True)

    # NOTE (guest checkout):
    # For guests we create Address rows with user=None only to snapshot the order's addresses.
    # They are not queryable by guest_token and not intended for reuse. Frontend re-sends full address on each order.
    # FUTURE (if needed): add guest_token field here to allow listing previous guest addresses before login.
    def __str__(self):
        return f"{self.full_name}, {self.line1}, {self.city}"


# ---- Coupon / CartCoupon ----
class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (("percent", "Percent"), ("fixed", "Fixed Amount"))

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    is_active = models.BooleanField(default=True, db_index=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total times this coupon can be used.")
    used_count = models.PositiveIntegerField(default=0)
    min_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self, subtotal: Decimal) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False
        if quantize_money(subtotal) < quantize_money(self.min_subtotal):
            return False
        return True

    def apply(self, subtotal: Decimal) -> Decimal:
        """Return discount amount (not exceeding subtotal)."""
        if not self.is_valid(subtotal):
            return Decimal("0.00")
        subtotal = quantize_money(subtotal)
        if self.discount_type == "percent":
            amt = (subtotal * self.value / Decimal("100")).quantize(TWO_PLACES)
        else:
            amt = quantize_money(self.value)
        return quantize_money(min(amt, subtotal))

    def increment_usage(self):
        """Atomically increment used_count; safe under concurrency."""
        with transaction.atomic():
            type(self).objects.filter(pk=self.pk).update(used_count=F("used_count") + 1)
            self.refresh_from_db(fields=["used_count"])


class CartCoupon(models.Model):
    """Track a coupon applied to a Cart."""
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="applied_coupon")
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="cart_applied")
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        owner = self.cart.user.email if self.cart.user else f"guest:{self.cart.guest_token}"
        return f"{owner} -> {self.coupon.code}"

    class Meta:
        verbose_name = "Cart Coupon"
        verbose_name_plural = "Cart Coupons"

    @staticmethod
    def get_applied(cart: Cart):
        return getattr(cart, "applied_coupon", None)

    @staticmethod
    def apply(code: str, cart: Cart) -> bool:
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return False
        subtotal = cart.subtotal()
        if not coupon.is_valid(subtotal):
            return False
        existing = CartCoupon.get_applied(cart)
        if existing:
            existing.coupon = coupon
            existing.save(update_fields=["coupon"])
        else:
            CartCoupon.objects.create(cart=cart, coupon=coupon)
        return True

    @staticmethod
    def remove(cart: Cart) -> bool:
        obj = CartCoupon.get_applied(cart)
        if obj:
            obj.delete()
            return True
        return False


# ---- Orders ----
def _generate_order_number() -> str:
    # Example: ORD-<uuid4 hex 12>
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


class Order(models.Model):
    order_number = models.CharField(max_length=40, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    guest_email = models.EmailField(null=True, blank=True)
    guest_token = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID,
                                      db_index=True)

    currency = models.CharField(max_length=10, default="BDT")
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    coupon_code = models.CharField(max_length=50, blank=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")

    notes = models.TextField(blank=True)

    shipping_address = models.ForeignKey("Address", on_delete=models.PROTECT, related_name="shipping_orders",
                                         null=True, blank=True)
    billing_address = models.ForeignKey("Address", on_delete=models.PROTECT, related_name="billing_orders",
                                        null=True, blank=True)

    shipping_method = models.ForeignKey("master.ShippingMethod", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    shipping_method_name = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Generate order_number automatically
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Ensure uniqueness collision extremely unlikely
            for _ in range(5):
                candidate = _generate_order_number()
                if not type(self).objects.filter(order_number=candidate).exists():
                    self.order_number = candidate
                    break
            if not self.order_number:
                # fallback to UUID
                self.order_number = f"ORD-{uuid.uuid4().hex}"
        super().save(*args, **kwargs)

    def clean(self):
        if not self.user and not self.guest_email:
            raise ValidationError("Either user or guest_email must be provided for an order.")
        if self.user and self.guest_email:
            raise ValidationError("Do not provide guest_email when the order has a user.")
        if self.coupon and not self.coupon.is_valid(self.subtotal_amount):
            raise ValidationError({"coupon": "Coupon is not valid for current subtotal."})
        if self.total_amount and self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative.")

    def recalculate_totals(self, persist: bool = False):
        """Compute subtotal, discount, tax and total from items & coupon snapshot."""
        agg = self.items.aggregate(total=Sum("line_total"))
        subtotal = Decimal(agg.get("total") or Decimal("0.00"))
        self.subtotal_amount = quantize_money(subtotal)

        discount = Decimal("0.00")
        if self.coupon:
            discount = self.coupon.apply(self.subtotal_amount)
        self.discount_amount = quantize_money(discount)

        # shipping_amount & tax_amount are expected to be set externally or default 0
        self.shipping_amount = quantize_money(self.shipping_amount)
        self.tax_amount = quantize_money(self.tax_amount)

        self.total_amount = quantize_money(
            self.subtotal_amount - self.discount_amount + self.shipping_amount + self.tax_amount
        )

        if persist:
            self.save(update_fields=["subtotal_amount", "discount_amount", "shipping_amount", "tax_amount", "total_amount"])

    def apply_coupon(self, code: str) -> bool:
        """Attach a valid coupon by code and recalc. Returns success status."""
        # Ensure latest subtotal before validation
        self.recalculate_totals(persist=False)
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return False
        if not coupon.is_valid(self.subtotal_amount):
            return False
        self.coupon = coupon
        self.coupon_code = coupon.code
        self.recalculate_totals(persist=True)
        return True

    def can_cancel(self):
        return self.status in {OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING}

    def cancel(self, reason: str = ""):
        if not self.can_cancel():
            raise ValidationError("Order cannot be cancelled at this stage.")
        self.status = OrderStatus.CANCELLED
        if reason:
            self.notes = (self.notes + "\nCancel: " + reason) if self.notes else ("Cancel: " + reason)
        self.save(update_fields=["status", "notes"])

    def mark_paid(self, transaction_id: str = "", method: str = PaymentMethod.COD):
        """Convenience: mark order paid and optionally create a Payment record."""
        self.payment_status = PaymentStatus.PAID
        self.save(update_fields=["payment_status"])
        if transaction_id:
            Payment.objects.create(
                order=self,
                method=method,
                status=PaymentStatus.PAID,
                amount=self.total_amount,
                currency=self.currency,
                transaction_id=transaction_id,
                paid_at=timezone.now(),
            )

    @classmethod
    def create_from_cart(cls, cart: Optional[Cart] = None, user: Optional[CustomUser] = None,
                         guest_token: Optional[str] = None, guest_email: Optional[str] = None,
                         shipping_address: Optional['Address'] = None,
                         billing_address: Optional['Address'] = None,
                         shipping_method: Optional['master.ShippingMethod'] = None,
                         currency: str = "BDT"):
        """
        Create an Order from the given cart (preferred).
        Backward-compat: if cart is None, resolve from user/guest_token.
        This method:
         - validates stock (fails if insufficient and backorder not allowed),
         - locks variants rows (select_for_update) while decrementing stock,
         - applies cart coupon,
         - increments coupon usage atomically,
         - clears cart items and coupon.
        """
        # Resolve cart
        if cart is None:
            if user and guest_token:
                raise ValidationError("Provide either user or guest_token, not both.")
            if not user and not guest_token:
                raise ValidationError("Either cart or (user/guest_token) must be provided.")
            cart = Cart.objects.for_owner(user=user, guest_token=guest_token)
            if not cart:
                raise ValidationError("Cart is empty.")

        cart_items = list(cart.items.select_related("variant", "variant__product").all())
        if not cart_items:
            raise ValidationError("Cart is empty.")

        with transaction.atomic():
            # Lock all involved ProductVariant rows to avoid races when decrementing stock
            variant_ids = [ci.variant_id for ci in cart_items if ci.variant_id]
            # Only lock if variant ids present
            if variant_ids:
                # Use ORM select_for_update via model manager and force evaluation to acquire lock
                variant_model = type(cart_items[0].variant)
                locked_qs = variant_model.objects.select_for_update().filter(pk__in=variant_ids)
                # force evaluation to obtain locks
                locked_qs.count()

            # Create order header
            order = cls.objects.create(
                user=cart.user,
                guest_email=guest_email if not cart.user else None,
                guest_token=cart.guest_token if not cart.user else None,
                currency=currency,
                shipping_address=shipping_address,
                billing_address=billing_address,
                shipping_method=shipping_method,
            )
            
            if shipping_method:
                order.shipping_method_name = shipping_method.name
                # Calculate shipping charge
                shipping_charge = shipping_method.base_cost
                # Threshold check
                if shipping_method.free_shipping_threshold is not None:
                    # We'll calculate threshold after items are summed, 
                    # but for now we initialize it
                    pass
                order.shipping_amount = quantize_money(shipping_charge)

            subtotal = Decimal("0.00")
            # Validate & create order items, decrement stock where applicable
            for item in cart_items:
                variant = item.variant
                if not variant:
                    raise ValidationError("Cart contains an invalid variant.")
                # Validate stock (respect variant.product.allow_backorder)
                variant_stock = getattr(variant, "stock", None)
                allow_backorder = getattr(variant.product, "allow_backorder", False)
                if variant_stock is not None and not allow_backorder and item.quantity > variant_stock:
                    raise ValidationError(f"Not enough stock for SKU {variant.sku}. Requested {item.quantity}, available {variant_stock}.")

                unit_price = quantize_money(item.get_unit_price())
                line_total = quantize_money(unit_price * item.quantity)
                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    product_name=getattr(variant.product, "name", "") or "",
                    sku=variant.sku or "",
                    unit_price=unit_price,
                    quantity=item.quantity,
                    line_total=line_total,
                )
                subtotal += line_total

                # Decrement variant.stock atomically if model has stock field
                if variant_stock is not None:
                    # Only decrement DB stock when backorder NOT allowed.
                    # This prevents writing negative stock (DB enforces stock >= 0).
                    if not allow_backorder:
                        updated = type(variant).objects.filter(pk=variant.pk, stock__gte=item.quantity).update(stock=F('stock') - item.quantity)
                        if updated == 0:
                            # concurrent change made stock insufficient
                            raise ValidationError(f"Insufficient stock for SKU {variant.sku} during order creation.")
                    else:
                        # Backorders allowed -> do NOT decrement the DB stock field to avoid negative values.
                        # If you need to track backorders, implement a separate field (e.g., backordered_quantity) and update it here.
                        pass

            order.subtotal_amount = quantize_money(subtotal)

            # Apply cart coupon if present and valid
            cart_coupon = getattr(cart, "applied_coupon", None)
            if cart_coupon and cart_coupon.coupon.is_valid(order.subtotal_amount):
                order.coupon = cart_coupon.coupon
                order.coupon_code = cart_coupon.coupon.code
                order.discount_amount = quantize_money(cart_coupon.coupon.apply(order.subtotal_amount))

            # Re-check free shipping threshold after subtotal is known
            if shipping_method and shipping_method.free_shipping_threshold is not None:
                if order.subtotal_amount >= shipping_method.free_shipping_threshold:
                    order.shipping_amount = Decimal("0.00")

            order.total_amount = quantize_money(order.subtotal_amount - order.discount_amount + order.shipping_amount + order.tax_amount)
            order.save()

            # Clear cart items and coupon. We keep the Cart container (for reuse).
            cart.items.all().delete()
            if cart_coupon:
                # increment usage safely
                cart_coupon.coupon.increment_usage()
                cart_coupon.delete()

            return order

    @property
    def is_guest(self) -> bool:
        return self.user_id is None

    @property
    def owner_type(self) -> str:
        return "guest" if self.is_guest else "user"

    @property
    def owner_email(self) -> Optional[str]:
        return self.user.email if not self.is_guest else self.guest_email

    @property
    def owner_identifier(self) -> str:
        """Returns user id (as str) or guest_token for analytics/correlation."""
        return str(self.user_id) if not self.is_guest else (self.guest_token or "")

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["user"]),
            models.Index(fields=["guest_token"]),
            models.Index(fields=["status"]),
            models.Index(fields=["coupon_code"]),
            models.Index(fields=["payment_status"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="order_owner_xor",
                check=(
                    (Q(user__isnull=False) & Q(guest_email__isnull=True)) |
                    (Q(user__isnull=True) & Q(guest_email__isnull=False))
                ),
            ),
        ]


# New: OrderStatusLog model to keep full history of status/payment changes
class OrderStatusLog(models.Model):
    CHANGE_TYPE_STATUS = "status"
    CHANGE_TYPE_PAYMENT = "payment"
    CHANGE_TYPE_CHOICES = (
        (CHANGE_TYPE_STATUS, "Order Status"),
        (CHANGE_TYPE_PAYMENT, "Payment Status"),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    old_value = models.CharField(max_length=50, blank=True)
    new_value = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="order_status_changes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Order Status Log"
        verbose_name_plural = "Order Status Logs"

    def __str__(self):
        who = self.changed_by.get_display_name() if self.changed_by else "System"
        return f"{self.order.order_number}: {self.get_change_type_display()} {self.old_value} -> {self.new_value} by {who}"


# Register signal handlers (moved to apps/order/signals.py)
from . import signals  # noqa: F401


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("ecom.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="order_items")

    # Snapshot fields for historical integrity
    product_name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    line_total = models.DecimalField(max_digits=12, decimal_places=2, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} ({self.order.order_number})"

    def save(self, *args, **kwargs):
        # Ensure line_total consistent
        if not self.line_total:
            self.line_total = quantize_money(self.unit_price * self.quantity)
        super().save(*args, **kwargs)
        # Intentionally DO NOT call order.recalculate_totals here to avoid repeated expensive DB operations.
        # Recalculation should be done explicitly when necessary or via provided signals below.



# ---- Payment ----
class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="BDT")
    transaction_id = models.CharField(max_length=128, blank=True, db_index=True)
    gateway_response = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.method} - {self.status}"

    def clean(self):
        if self.amount is None or self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "Payment amount must be greater than 0."})
        if self.order and self.currency != self.order.currency:
            raise ValidationError({"currency": "Payment currency must match order currency."})

    def save(self, *args, **kwargs):
        # Normalize amount and set paid_at when status is PAID
        self.amount = quantize_money(self.amount)
        if self.status == PaymentStatus.PAID and not self.paid_at:
            self.paid_at = timezone.now()
        super().save(*args, **kwargs)
        # If payment is marked as paid, update order payment_status
        if self.order and self.status == PaymentStatus.PAID and self.order.payment_status != PaymentStatus.PAID:
            self.order.payment_status = PaymentStatus.PAID
            self.order.save(update_fields=["payment_status"])
