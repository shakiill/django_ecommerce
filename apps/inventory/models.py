from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.aggregates import Sum

from apps.helpers.models import UserTimestampMixin


class PurchaseRequisition(UserTimestampMixin):
    """
    Purchase requisition (PR) - internal request to purchase items.
    First step in inventory process.
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('partially_ordered', 'Partially Ordered'),
        ('ordered', 'Ordered'),
        ('cancelled', 'Cancelled'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    pr_number = models.CharField(max_length=100, unique=True, db_index=True)
    warehouse = models.ForeignKey('master.Warehouse', on_delete=models.PROTECT, related_name='purchase_requisitions')

    requisition_date = models.DateField()
    required_date = models.DateField(help_text='Date items are needed by')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')

    # Requester
    requested_by = models.ForeignKey('user.CustomUser', on_delete=models.PROTECT, related_name='requisitions')
    department = models.CharField(max_length=100, blank=True, null=True)

    # Approval workflow
    approved_by = models.ForeignKey('user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_requisitions')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Details
    purpose = models.TextField(help_text='Purpose/reason for requisition')
    notes = models.TextField(blank=True, null=True)

    # Totals
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    status_history = models.JSONField(default=list, blank=True, null=True)

    class Meta:
        verbose_name = 'Purchase Requisition'
        verbose_name_plural = 'Purchase Requisitions'
        ordering = ['-requisition_date', '-created_at']
        indexes = [
            models.Index(fields=['pr_number']),
            models.Index(fields=['status', '-requisition_date']),
        ]

    def __str__(self):
        return f"{self.pr_number} - {self.status}"

    def log_status_change(self, old_status: str, new_status: str, user=None, note: str = None):
        """
        Append a status change record to status_history (does not save).
        Record format: {from, from_display, to, to_display, changed_by_id, changed_by, timestamp, note}
        """
        from django.utils import timezone

        if self.status_history is None:
            self.status_history = []

        # helper to get display label from choices for this model
        def _label_for(status_val):
            for val, lbl in getattr(self, 'STATUS_CHOICES', ()):
                if val == status_val:
                    return lbl
            return status_val

        entry = {
            'from': old_status,
            'from_display': _label_for(old_status),
            'to': new_status,
            'to_display': _label_for(new_status),
            'changed_by_id': getattr(user, 'pk', None),
            'changed_by': str(user) if user else None,
            'timestamp': timezone.now().isoformat(),
            'note': note,
        }
        self.status_history.append(entry)
        # do not save here; caller will save with desired update_fields


class PurchaseRequisitionItem(UserTimestampMixin):
    """Items in a purchase requisition"""
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.PROTECT)

    quantity_requested = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_ordered = models.IntegerField(default=0, help_text='Quantity already in POs')

    estimated_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    specifications = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Purchase Requisition Item'
        verbose_name_plural = 'Purchase Requisition Items'
        unique_together = ('requisition', 'product_variant')

    def __str__(self):
        return f"{self.requisition.pr_number} - {self.product_variant.sku}"

    def save(self, *args, **kwargs):
        self.estimated_total = self.quantity_requested * self.estimated_unit_price
        super().save(*args, **kwargs)


class PurchaseOrder(UserTimestampMixin):
    """
    Purchase Order (PO) sent to suppliers.
    Can be created from requisitions or directly.
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed by Supplier'),
        ('partially_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    )

    po_number = models.CharField(max_length=100, unique=True, db_index=True)
    supplier = models.ForeignKey('master.Supplier', on_delete=models.PROTECT, related_name='purchase_orders')
    warehouse = models.ForeignKey('master.Warehouse', on_delete=models.PROTECT, related_name='purchase_orders')

    order_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # References
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='purchase_orders')
    supplier_reference = models.CharField(max_length=100, blank=True, null=True,
                                          help_text='Supplier order/quote reference')

    # Payment terms
    payment_method = models.ForeignKey('master.PaymentMethod', on_delete=models.SET_NULL, null=True, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)

    # Shipping
    shipping_method = models.ForeignKey('master.ShippingMethod', on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address = models.TextField()
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Additional
    notes = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)

    # Approval
    approved_by = models.ForeignKey('user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_pos')
    approved_at = models.DateTimeField(null=True, blank=True)

    status_history = models.JSONField(default=list, blank=True, null=True)

    class Meta:
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-order_date', '-created_at']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['supplier', '-order_date']),
            models.Index(fields=['status', '-order_date']),
        ]

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

    @property
    def additional_cost_total(self):
        # Sum of related AdditionalCost amounts
        return sum((c.amount for c in self.additional_costs.all()), Decimal('0.00'))

    def log_status_change(self, old_status: str, new_status: str, user=None, note: str = None):
        """
        Append a status change record to status_history (does not save).
        """
        from django.utils import timezone

        if self.status_history is None:
            self.status_history = []

        def _label_for(status_val):
            for val, lbl in getattr(self, 'STATUS_CHOICES', ()):
                if val == status_val:
                    return lbl
            return status_val

        entry = {
            'from': old_status,
            'from_display': _label_for(old_status),
            'to': new_status,
            'to_display': _label_for(new_status),
            'changed_by_id': getattr(user, 'pk', None),
            'changed_by': str(user) if user else None,
            'timestamp': timezone.now().isoformat(),
            'note': note,
        }
        self.status_history.append(entry)
        # do not save here; caller will save with desired update_fields


class PurchaseOrderItem(UserTimestampMixin):
    """Items in a purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.PROTECT)

    quantity_ordered = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_received = models.IntegerField(default=0)
    quantity_cancelled = models.IntegerField(default=0)

    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0.000'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
        unique_together = ('purchase_order', 'product_variant')

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product_variant.sku}"

    def save(self, *args, **kwargs):
        # Calculate amounts
        subtotal = self.quantity_ordered * self.unit_price
        self.discount_amount = subtotal * (self.discount_percent / 100)
        amount_after_discount = subtotal - self.discount_amount
        self.tax_amount = amount_after_discount * (self.tax_rate / 100)
        self.line_total = amount_after_discount + self.tax_amount
        super().save(*args, **kwargs)


class AdditionalCost(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='additional_costs')
    description = models.CharField(max_length=100)  # Description of the additional cost
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.description} - {self.amount} for PO {self.purchase_order.id}"

class GoodsReceiptNote(UserTimestampMixin):
    """
    GRN - Records receipt of goods from suppliers.
    On approval, updates Stock automatically.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('inspected', 'Quality Inspected'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('partially_accepted', 'Partially Accepted'),
    ]

    grn_number = models.CharField(max_length=100, unique=True, db_index=True)
    purchase_order = models.ForeignKey('inventory.PurchaseOrder', on_delete=models.PROTECT, related_name='grns')
    warehouse = models.ForeignKey('master.Warehouse', on_delete=models.PROTECT, related_name='grns')
    receipt_date = models.DateField()

    received_by = models.ForeignKey('user.CustomUser', on_delete=models.PROTECT, related_name='received_grns')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    carrier = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField(null=True, blank=True)

    inspected_by = models.ForeignKey('user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='inspected_grns')
    inspection_date = models.DateField(null=True, blank=True)
    inspection_notes = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Goods Receipt Note'
        verbose_name_plural = 'Goods Receipt Notes'
        ordering = ['-receipt_date', '-created_at']

    def __str__(self):
        return f"{self.grn_number} - {self.purchase_order.po_number}"

    def update_stock(self):
        """Apply GRN quantities to stock (called when accepted)."""
        for item in self.items.all():
            accepted_qty = Decimal(item.quantity_accepted or 0)
            if accepted_qty > 0:
                stock, _ = Stock.objects.get_or_create(
                    product_variant=item.product_variant,
                    warehouse=self.warehouse,
                    defaults={'quantity_on_hand': 0, 'quantity_reserved': 0}
                )
                stock.quantity_on_hand += accepted_qty
                stock.save(update_fields=['quantity_on_hand'])
                StockMovement.objects.create(
                    product_variant=item.product_variant,
                    warehouse=self.warehouse,
                    movement_type='in',
                    quantity=accepted_qty,
                    reference=f"GRN-{self.id}"
                )


class GoodsReceiptNoteItem(UserTimestampMixin):
    CONDITION_CHOICES = [
        ('good', 'Good Condition'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective'),
        ('expired', 'Expired'),
    ]

    grn = models.ForeignKey(GoodsReceiptNote, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey('inventory.PurchaseOrderItem', on_delete=models.PROTECT)
    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.PROTECT)

    quantity_ordered = models.IntegerField()
    quantity_received = models.IntegerField(validators=[MinValueValidator(0)])
    quantity_accepted = models.IntegerField(default=0)
    quantity_rejected = models.IntegerField(default=0)

    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('grn', 'po_item')
        verbose_name = 'GRN Item'

    def __str__(self):
        return f"{self.grn.grn_number} - {self.product_variant.sku}"

    def save(self, *args, **kwargs):
        # Ensure accepted + rejected <= received
        if (self.quantity_accepted + self.quantity_rejected) > self.quantity_received:
            self.quantity_accepted = self.quantity_received - self.quantity_rejected
        super().save(*args, **kwargs)


class Stock(UserTimestampMixin):
    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.CASCADE, related_name='stocks')
    warehouse = models.ForeignKey('master.Warehouse', on_delete=models.CASCADE, related_name='stocks')
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ('product_variant', 'warehouse')
        verbose_name_plural = 'Stock'

    def __str__(self):
        return f"{self.product_variant} @ {self.warehouse}"

    @property
    def available_quantity(self):
        return self.quantity_on_hand - self.quantity_reserved


class StockMovement(UserTimestampMixin):
    MOVEMENT_TYPES = [
        ('in', 'In'),
        ('out', 'Out'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
    ]

    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.CASCADE)
    warehouse = models.ForeignKey('master.Warehouse', on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    reference = models.CharField(max_length=50, null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.movement_type} {self.product_variant} ({self.quantity})"

class StockAdjustment(UserTimestampMixin):
    ADJUSTMENT_TYPES = [
        ('opening', 'Opening Stock'),
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
        ('correction', 'Correction'),
    ]

    warehouse = models.ForeignKey('master.Warehouse', on_delete=models.CASCADE)
    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    def apply(self):
        stock, _ = Stock.objects.get_or_create(
            product_variant=self.product_variant,
            warehouse=self.warehouse,
            defaults={'quantity_on_hand': 0, 'quantity_reserved': 0}
        )

        stock.quantity_on_hand += self.quantity
        stock.save(update_fields=['quantity_on_hand'])

        StockMovement.objects.create(
            product_variant=self.product_variant,
            warehouse=self.warehouse,
            movement_type='adjustment',
            quantity=self.quantity,
            reference=f"ADJ-{self.id}"
        )

    def __str__(self):
        return f"{self.adjustment_type} - {self.product_variant} @ {self.warehouse}"


class StockTransfer(UserTimestampMixin):
    reference_no = models.CharField(max_length=30, unique=True, blank=True)
    source_warehouse = models.ForeignKey('master.Warehouse', on_delete=models.CASCADE, related_name='transfers_out')
    destination_warehouse = models.ForeignKey('master.Warehouse', on_delete=models.CASCADE, related_name='transfers_in')
    remarks = models.TextField(blank=True, null=True)

    def transfer(self):
        for item in self.items.all():
            src_stock, _ = Stock.objects.get_or_create(
                product_variant=item.product_variant,
                warehouse=self.source_warehouse,
                defaults={'quantity_on_hand': 0}
            )
            dest_stock, _ = Stock.objects.get_or_create(
                product_variant=item.product_variant,
                warehouse=self.destination_warehouse,
                defaults={'quantity_on_hand': 0}
            )
            src_stock.quantity_on_hand -= item.quantity
            dest_stock.quantity_on_hand += item.quantity
            src_stock.save(update_fields=['quantity_on_hand'])
            dest_stock.save(update_fields=['quantity_on_hand'])
            # record movement
            StockMovement.objects.bulk_create([
                StockMovement(
                    product_variant=item.product_variant,
                    warehouse=self.source_warehouse,
                    movement_type='out',
                    quantity=-item.quantity,
                    reference=f"TRF-{self.id}"
                ),
                StockMovement(
                    product_variant=item.product_variant,
                    warehouse=self.destination_warehouse,
                    movement_type='in',
                    quantity=item.quantity,
                    reference=f"TRF-{self.id}"
                )
            ])

    def __str__(self):
        return f"Transfer {self.reference_no or self.id}"


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('ecom.ProductVariant', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])


class StockAlert(UserTimestampMixin):
    product_variant = models.OneToOneField('ecom.ProductVariant', on_delete=models.CASCADE)
    min_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def check_alert(self):
        total_stock = Stock.objects.filter(product_variant=self.product_variant).aggregate(
            total=Sum('quantity_on_hand')
        )['total'] or 0
        return total_stock <= self.min_quantity
