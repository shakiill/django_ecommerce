from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.apps import apps


@receiver(pre_save)
def order_pre_save(sender, instance, **kwargs):
    """
    Capture previous status/payment_status before save so post_save can detect changes.
    Only act for Order model from this app to avoid importing models at module load time.
    """
    if instance._meta.app_label != "order" or instance._meta.model_name != "order":
        return

    if not instance.pk:
        instance._old_status = None
        instance._old_payment_status = None
    else:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_payment_status = old.payment_status
        except sender.DoesNotExist:
            instance._old_status = None
            instance._old_payment_status = None


@receiver(post_save)
def order_post_save(sender, instance, created, **kwargs):
    """
    Create OrderStatusLog entries when status or payment_status change.
    If callers set instance._log_skip = True they manage logging themselves.
    """
    if instance._meta.app_label != "order" or instance._meta.model_name != "order":
        return

    if getattr(instance, "_log_skip", False):
        return

    old_status = getattr(instance, "_old_status", None)
    old_payment = getattr(instance, "_old_payment_status", None)

    OrderStatusLog = apps.get_model("order", "OrderStatusLog")

    if old_status != instance.status:
        OrderStatusLog.objects.create(
            order=instance,
            change_type=OrderStatusLog.CHANGE_TYPE_STATUS,
            old_value=(old_status or ""),
            new_value=(instance.status or ""),
            changed_by=None,
        )

    if old_payment != instance.payment_status:
        OrderStatusLog.objects.create(
            order=instance,
            change_type=OrderStatusLog.CHANGE_TYPE_PAYMENT,
            old_value=(old_payment or ""),
            new_value=(instance.payment_status or ""),
            changed_by=None,
        )


@receiver(post_delete)
def orderitem_deleted(sender, instance, **kwargs):
    """
    When an order item is deleted, recalculate order totals.
    Only act for OrderItem model from this app.
    """
    if instance._meta.app_label != "order" or instance._meta.model_name != "orderitem":
        return

    if instance.order_id:
        try:
            instance.order.recalculate_totals(persist=True)
        except Exception:
            # ignore if order cannot be found or recalculation fails
            pass
