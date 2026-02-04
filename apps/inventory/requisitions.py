from datetime import datetime

from django.db.models import Max

from apps.inventory.models import PurchaseRequisition


def generate_pr_number(prefix: str = "PR") -> str:
    """
    Generate a unique PR number with format: PR-YYYYMMDD-XXXX
    Where XXXX is a zero-padded incremental counter per day.
    """
    today = datetime.now().strftime('%Y%m%d')
    day_prefix = f"{prefix}-{today}"

    # Find max sequence for today
    latest = (PurchaseRequisition.objects
              .filter(pr_number__startswith=day_prefix)
              .aggregate(max_seq=Max('pr_number'))['max_seq'])

    if latest:
        try:
            last_seq = int(str(latest).split('-')[-1])
        except Exception:
            last_seq = 0
    else:
        last_seq = 0

    next_seq = last_seq + 1
    return f"{day_prefix}-{next_seq:04d}"


def recalc_requisition_total(requisition: PurchaseRequisition) -> None:
    """Recalculate and persist total_amount for a requisition."""
    total = sum((item.estimated_total for item in requisition.items.all()), start=0)
    requisition.total_amount = total
    requisition.save(update_fields=['total_amount'])

