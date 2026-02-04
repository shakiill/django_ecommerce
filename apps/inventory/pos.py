from datetime import datetime
from decimal import Decimal

from django.db.models import Max

from apps.inventory.models import PurchaseOrder, PurchaseRequisition, PurchaseRequisitionItem, PurchaseOrderItem


def generate_po_number(prefix: str = "PO") -> str:
    """Generate a unique PO number like PO-YYYYMMDD-XXXX."""
    today = datetime.now().strftime('%Y%m%d')
    day_prefix = f"{prefix}-{today}"

    latest = (PurchaseOrder.objects
              .filter(po_number__startswith=day_prefix)
              .aggregate(max_seq=Max('po_number'))['max_seq'])

    if latest:
        try:
            last_seq = int(str(latest).split('-')[-1])
        except Exception:
            last_seq = 0
    else:
        last_seq = 0

    next_seq = last_seq + 1
    return f"{day_prefix}-{next_seq:04d}"


def recalc_po_totals(po: PurchaseOrder) -> None:
    """Recalculate and persist PO totals from items, shipping, and additional costs."""
    subtotal = Decimal('0.00')
    discount_total = Decimal('0.00')
    tax_total = Decimal('0.00')

    for it in po.items.all():
        # PurchaseOrderItem.save() already sets line_total, discount_amount, tax_amount
        subtotal += (it.quantity_ordered * it.unit_price)
        discount_total += (it.discount_amount or Decimal('0.00'))
        tax_total += (it.tax_amount or Decimal('0.00'))

    additional_total = sum((ac.amount for ac in po.additional_costs.all()), Decimal('0.00'))

    po.subtotal = subtotal
    po.discount_amount = discount_total
    po.tax_amount = tax_total
    po.total_amount = subtotal - discount_total + tax_total + (po.shipping_cost or Decimal('0.00')) + additional_total
    po.save(update_fields=['subtotal', 'discount_amount', 'tax_amount', 'total_amount'])


def update_requisition_ordered(requisition: PurchaseRequisition) -> None:
    """Update PR items' quantity_ordered and PR status based on linked POs."""
    if not requisition:
        return
    # Reset all to 0 then recompute from POs
    pr_items = {ri.product_variant_id: ri for ri in requisition.items.all()}
    for ri in pr_items.values():
        ri.quantity_ordered = 0
        ri.save(update_fields=['quantity_ordered'])

    linked_pos = PurchaseOrder.objects.filter(requisition=requisition)
    for po in linked_pos.prefetch_related('items'):
        for poi in po.items.all():
            ri = pr_items.get(poi.product_variant_id)
            if ri:
                ri.quantity_ordered += poi.quantity_ordered
                ri.save(update_fields=['quantity_ordered'])

    # Determine status
    total = sum(ri.quantity_requested for ri in pr_items.values()) or 0
    ordered = sum(ri.quantity_ordered for ri in pr_items.values()) or 0
    if ordered == 0:
        requisition.status = 'approved' if requisition.status in ('approved', 'submitted', 'draft') else requisition.status
    elif ordered < total:
        requisition.status = 'partially_ordered'
    else:
        requisition.status = 'ordered'
    requisition.save(update_fields=['status'])
