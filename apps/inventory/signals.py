from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.inventory.models import (
    GoodsReceiptNote, StockAdjustment, StockTransfer, Stock, StockMovement
)


# -------------------------------
# GRN: Auto apply stock on acceptance
# -------------------------------
@receiver(post_save, sender=GoodsReceiptNote)
def grn_auto_apply(sender, instance, **kwargs):
    """
    When a GRN is saved and status is 'accepted' or 'partially_accepted',
    update stock for all GRN items.
    """
    if instance.status in ('accepted', 'partially_accepted'):
        for item in instance.items.all():
            accepted_qty = Decimal(item.quantity_accepted or 0)
            if accepted_qty > 0:
                stock, _ = Stock.objects.get_or_create(
                    product_variant=item.product_variant,
                    warehouse=instance.warehouse,
                    defaults={'quantity_on_hand': 0, 'quantity_reserved': 0}
                )
                stock.quantity_on_hand += accepted_qty
                stock.save(update_fields=['quantity_on_hand'])

                StockMovement.objects.create(
                    product_variant=item.product_variant,
                    warehouse=instance.warehouse,
                    movement_type='in',
                    quantity=accepted_qty,
                    reference=f"GRN-{instance.id}"
                )


# -------------------------------
# Stock Adjustment: Auto apply on create
# -------------------------------
@receiver(post_save, sender=StockAdjustment)
def stock_adjustment_auto_apply(sender, instance, created, **kwargs):
    """
    When a StockAdjustment is created, automatically update stock.
    """
    if created:
        stock, _ = Stock.objects.get_or_create(
            product_variant=instance.product_variant,
            warehouse=instance.warehouse,
            defaults={'quantity_on_hand': 0, 'quantity_reserved': 0}
        )
        stock.quantity_on_hand += instance.quantity
        stock.save(update_fields=['quantity_on_hand'])

        StockMovement.objects.create(
            product_variant=instance.product_variant,
            warehouse=instance.warehouse,
            movement_type='adjustment',
            quantity=instance.quantity,
            reference=f"ADJ-{instance.id}"
        )


# -------------------------------
# Stock Transfer: Auto apply on create
# -------------------------------
@receiver(post_save, sender=StockTransfer)
def stock_transfer_auto_apply(sender, instance, created, **kwargs):
    """
    When a StockTransfer is created, move stock from source to destination.
    """
    if created:
        for item in instance.items.all():
            # Source stock
            src_stock, _ = Stock.objects.get_or_create(
                product_variant=item.product_variant,
                warehouse=instance.source_warehouse,
                defaults={'quantity_on_hand': 0}
            )
            # Destination stock
            dest_stock, _ = Stock.objects.get_or_create(
                product_variant=item.product_variant,
                warehouse=instance.destination_warehouse,
                defaults={'quantity_on_hand': 0}
            )

            src_stock.quantity_on_hand -= item.quantity
            dest_stock.quantity_on_hand += item.quantity

            src_stock.save(update_fields=['quantity_on_hand'])
            dest_stock.save(update_fields=['quantity_on_hand'])

            # Record movements
            StockMovement.objects.bulk_create([
                StockMovement(
                    product_variant=item.product_variant,
                    warehouse=instance.source_warehouse,
                    movement_type='out',
                    quantity=-item.quantity,
                    reference=f"TRF-{instance.id}"
                ),
                StockMovement(
                    product_variant=item.product_variant,
                    warehouse=instance.destination_warehouse,
                    movement_type='in',
                    quantity=item.quantity,
                    reference=f"TRF-{instance.id}"
                )
            ])
