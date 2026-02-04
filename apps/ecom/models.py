import random
import string
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify

from apps.helpers.models import UserTimestampMixin
from apps.master.models import Category, Brand, Tag, AttributeValue, Tax, Unit


class Product(UserTimestampMixin):
    """
    Core product model containing base information.
    Pricing, stock, and SKU data are managed at the ProductVariant level.
    Every product MUST have at least one variant.
    """
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=300, unique=True, db_index=True, editable=True, blank=True)
    description = models.TextField(null=True, blank=True)
    short_description = models.TextField(max_length=500, null=True, blank=True)
    key_features = models.TextField(default='', blank=True)  # Product Key Features
    min_order_quantity = models.PositiveIntegerField(default=1)  # Minimum order quantity
    max_order_quantity = models.PositiveIntegerField(default=100)  # Maximum order quantity

    # Relationships
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='cat_products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='b_products')

    # Default physical properties (can be overridden by variants)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True,
                                 help_text='Default weight in kg')
    dimensions = models.JSONField(null=True, blank=True, help_text='Default dimensions (L, W, H) in cm')

    # Product type and inventory settings
    product_type = models.CharField(max_length=50, choices=[('physical', 'Physical'), ('digital', 'Digital')],
                                    default='physical')
    track_inventory = models.BooleanField(default=True)
    allow_backorder = models.BooleanField(default=True)

    # Status flags
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    # SEO
    meta_title = models.CharField(max_length=200, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)

    # Many-to-many
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')

    # The primary variant used for display and direct "add to cart" actions.
    default_variant = models.OneToOneField('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='+')

    # Add thumbnail image for product
    thumbnail = models.ImageField(upload_to='products/thumbnails/', null=True, blank=True)
    thumbnail_hover = models.ImageField(upload_to='products/thumbnails/', null=True, blank=True)

    # Indicates if the product has variants
    is_variant = models.BooleanField(default=True, help_text="Does this product have variants?")
    selling_tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True, related_name='t_products')
    tax_type = models.CharField(max_length=50, choices=[('inclusive', 'Inclusive'), ('exclusive', 'Exclusive')],
                                default='exclusive')
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,
                                        help_text="Default profit margin percentage for this product.")
    warranty = models.CharField(max_length=255, null=True, blank=True)  # Warranty information
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True,)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            slug_base = slugify(self.name)
            unique_suffix = ''.join(random.choices(string.digits, k=4))
            self.slug = f"{slug_base}-{unique_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_price(self):
        """Returns the price of the default variant."""
        if self.default_variant:
            return self.default_variant.price
        first_variant = self.variants.filter(is_active=True).first()
        return first_variant.price if first_variant else Decimal('0.00')

    def get_total_stock(self, warehouse=None):
        if not self.track_inventory:
            return None
        from apps.inventory.models import Stock
        variants = self.variants.filter(is_active=True)
        filters = {'product_variant__in': variants}
        if warehouse:
            filters['warehouse'] = warehouse
        total = Stock.objects.filter(**filters).aggregate(total=Sum('quantity_on_hand'))['total'] or 0
        return total

    def is_in_stock(self, warehouse=None):
        if not self.track_inventory:
            return True
        stock = self.get_total_stock(warehouse)
        return stock > 0 if stock is not None else self.allow_backorder


class ProductVariant(UserTimestampMixin):
    """
    Represents a specific version of a Product (SKU).
    All pricing, stock, and unique identifiers live here.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=255, help_text='e.g., "Red (M)"', blank=True)
    sku = models.CharField(max_length=120, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                         help_text="Purchase cost for this variant.")
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    # Discount fields
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                         help_text="Discounted price for this variant.")
    is_discount = models.BooleanField(default=False, help_text="Is discount active for this variant?")
    discount_start = models.DateTimeField(null=True, blank=True, help_text="Discount start datetime.")
    discount_end = models.DateTimeField(null=True, blank=True, help_text="Discount end datetime.")
    # Inventory
    stock = models.PositiveIntegerField(default=0)
    # Physical properties (overrides product defaults)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, help_text='Weight in kg')
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    # Variant attributes
    attributes = models.ManyToManyField(AttributeValue, blank=True)
    # Add main image for variant
    image = models.ImageField(upload_to='products/variants/', null=True, blank=True)  # this will not use,

    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        ordering = ['product', 'sku']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product', 'is_active']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.variant_name or self.sku}"

    def save(self, *args, **kwargs):
        skip_gen = kwargs.pop('_skip_variant_name_generation', False)
        super().save(*args, **kwargs)
        if not skip_gen and (not self.variant_name or not self.variant_name.strip()):
            attrs = list(self.attributes.all()[:2])
            generated = None
            if len(attrs) == 1:
                generated = attrs[0].value
            elif len(attrs) >= 2:
                generated = f"{attrs[0].value} ({attrs[1].value})"
            if generated:
                type(self).objects.filter(pk=self.pk).update(variant_name=generated)
                self.variant_name = generated
        if not self.product.default_variant:
            self.product.default_variant = self
            self.product.save()

    @property
    def is_on_sale(self):
        return self.is_discount and self.discount_price is not None and self.discount_price < self.price

    def get_effective_weight(self):
        return self.weight or self.product.weight

    def get_stock_by_warehouse(self, warehouse):
        """Get stock for this variant in a specific warehouse."""
        from apps.inventory.models import Stock
        try:
            stock = Stock.objects.get(product_variant=self, warehouse=warehouse)
            return stock.available_quantity
        except Stock.DoesNotExist:
            return 0

    def get_total_stock(self):
        """Get total stock across all warehouses."""
        from apps.inventory.models import Stock
        result = Stock.objects.filter(product_variant=self).aggregate(
            total=Sum('quantity_on_hand')
        )
        return result['total'] or 0

    def update_stock_on_hand(self):
        """
        Legacy method for backward compatibility.
        Now stock is managed in Stock model per warehouse.
        This updates the variant's stock field as a summary.
        """
        self.stock = self.get_total_stock()
        self.save(update_fields=['stock'])

    def get_effective_price(self):
        """Return discounted price if on sale else regular price."""
        if self.is_on_sale and self.discount_price:
            return self.discount_price
        return self.price

    def max_purchasable(self):
        """Return max quantity user can purchase respecting product & stock."""
        product = self.product
        if not product.track_inventory:
            return product.max_order_quantity
        stock = self.stock
        limit = min(stock, product.max_order_quantity) if stock is not None else product.max_order_quantity
        return max(product.min_order_quantity, limit)


class ProductImage(UserTimestampMixin):
    """
    Product images, which can be linked to a product or a specific variant.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    attributes = models.ManyToManyField(AttributeValue, blank=True,
                                        help_text="Attributes that already presents in ProductVariant.")
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['display_order']


# Signal handler: update variant_name when attributes M2M changes (covers attributes added after initial save)
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

def _generate_variant_name_from_instance(instance):
    vals = list(instance.attributes.all()[:2])
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0].value
    return f"{vals[0].value} ({vals[1].value})"

@receiver(m2m_changed, sender=ProductVariant.attributes.through)
def productvariant_attributes_changed(sender, instance, action, pk_set, **kwargs):
    # When attributes are added/removed/cleared, if variant_name is blank, generate it.
    if action in ('post_add', 'post_remove', 'post_clear'):
        if not instance.variant_name or not instance.variant_name.strip():
            gen = _generate_variant_name_from_instance(instance)
            if gen:
                # Use queryset update to avoid recursion into save()
                type(instance).objects.filter(pk=instance.pk).update(variant_name=gen)
                instance.variant_name = gen
