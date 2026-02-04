from decimal import Decimal
from django.utils.translation import gettext_lazy as _  # added import

from django.db import models
from django.utils.text import slugify

from apps.helpers.models import UserTimestampMixin
from apps.user.models import CustomUser, Staff


class Attribute(UserTimestampMixin):
    """Product attributes like Color, Size, Material"""
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Attribute'
        verbose_name_plural = 'Attributes'
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AttributeValue(UserTimestampMixin):
    """Values for attributes (e.g., Red, Blue for Color)"""
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=150)
    code = models.CharField(max_length=80, blank=True, null=True)
    color_code = models.CharField(max_length=7, blank=True, null=True, help_text='Hex color code for color attributes')
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('attribute', 'value')
        verbose_name = 'Attribute Value'
        verbose_name_plural = 'Attribute Values'
        ordering = ['attribute', 'display_order', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Tag(UserTimestampMixin):
    """Tags for products"""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    class Type(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual'
        BUSINESS = 'business', 'Business'

    # Core Identity
    contact_type = models.CharField(max_length=20, choices=Type.choices, default=Type.INDIVIDUAL)
    contact_id = models.CharField(max_length=80, unique=True, blank=True, null=True)

    # Individual Fields
    prefix = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Business Fields
    business_name = models.CharField(max_length=255, blank=True, null=True)

    # Contact Details
    mobile = models.CharField(max_length=50, blank=True, null=True)
    alternate_contact_number = models.CharField(max_length=50, blank=True, null=True)
    landline = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Financial Info
    tax_number = models.CharField(max_length=100, blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    pay_term = models.CharField(max_length=100, blank=True, null=True)
    pay_term_type = models.CharField(max_length=20, choices=[
        ('days', 'Days'),
        ('months', 'Months')
    ], blank=True, null=True)

    # Address Info
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)

    # Assigned User (like sales representative or account manager)
    assigned_to = models.ManyToManyField(Staff, blank=True, related_name='suppliers')

    # Custom Fields (10 placeholders)
    custom_field_1 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_2 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_3 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_4 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_5 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_6 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_7 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_8 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_9 = models.CharField(max_length=255, blank=True, null=True)
    custom_field_10 = models.CharField(max_length=255, blank=True, null=True)

    # Status & System
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['-created_at']

    def __str__(self):
        if self.contact_type == self.Type.BUSINESS and self.business_name:
            return self.business_name
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or "Unnamed Supplier"

    def clean(self):
        """
        Ensure minimal consistency before save.
        """
        # ensure mobile exists
        if not self.mobile:
            from django.core.exceptions import ValidationError
            raise ValidationError({'mobile': 'Mobile number is required for supplier.'})

    def _generate_contact_id(self):
        """
        Generate a unique contact_id if missing. Uses a compact uuid fragment.
        """
        import uuid
        base = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        # ensure uniqueness
        while Supplier.objects.filter(contact_id=base).exists():
            base = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        return base

    def save(self, *args, **kwargs):
        # generate contact_id if missing
        if not self.contact_id:
            self.contact_id = self._generate_contact_id()
        super(Supplier, self).save(*args, **kwargs)

    def get_display_name(self):
        """
        Prefer business_name for businesses, otherwise full person name.
        """
        if self.contact_type == self.Type.BUSINESS and self.business_name:
            return self.business_name
        parts = [p for p in (self.prefix, self.first_name, self.middle_name, self.last_name) if p]
        return " ".join(parts) or self.business_name or self.mobile


class Tax(UserTimestampMixin):
    """Tax definitions"""
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=80, unique=True)
    rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.000'))
    is_inclusive = models.BooleanField(default=False)
    is_compound = models.BooleanField(default=False, help_text='Applied after other taxes')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'

    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class Unit(UserTimestampMixin):
    """Unit of measure"""
    name = models.CharField(max_length=120, unique=True)
    short_name = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'

    def __str__(self):
        return self.name if not self.short_name else f"{self.name} ({self.short_name})"


class Brand(UserTimestampMixin):
    """Product brands"""
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(UserTimestampMixin):
    """Hierarchical product categories"""
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    parent = models.ManyToManyField('self', blank=True, related_name='children', symmetrical=False)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True, help_text='Icon class or name')
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            # Slugify using name only, as parent is now M2M
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Warehouse(UserTimestampMixin):
    """Warehouse/location for inventory"""
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=80, unique=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'

    def __str__(self):
        return self.name


class Currency(UserTimestampMixin):
    """Currency definitions"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=80)
    symbol = models.CharField(max_length=10, blank=True, null=True)
    rate_to_base = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('1.0'))
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.code} ({self.symbol or ''})"


class PaymentMethod(UserTimestampMixin):
    """Payment methods available"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    payment_type = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_payment', 'Mobile Payment'),
        ('wallet', 'Wallet'),
        ('cod', 'Cash on Delivery'),
        ('other', 'Other'),
    ])
    is_online = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    processing_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ShippingMethod(UserTimestampMixin):
    """Shipping methods"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    estimated_days_min = models.IntegerField(null=True, blank=True)
    estimated_days_max = models.IntegerField(null=True, blank=True)
    base_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    cost_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='If greater than 0, shipping cost is calculated as order_total * (rate_percent / 100).'
    )
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Shipping Method'
        verbose_name_plural = 'Shipping Methods'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name
