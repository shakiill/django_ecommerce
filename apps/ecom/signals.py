from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache

from apps.ecom.models import Product, ProductVariant, ProductImage


# Signal to create a default variant
@receiver(post_save, sender=Product)
def create_default_variant(sender, instance, created, **kwargs):
    if created and not instance.is_variant and not instance.default_variant:
        variant = ProductVariant.objects.create(
            product=instance,
            sku=f"{instance.slug}-default",
            price=0.00,
        )
        instance.default_variant = variant
        instance.save()
    # Invalidate product related cache keys
    _invalidate_product_cache(instance)


@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
def variant_changed(sender, instance, **kwargs):
    _invalidate_product_cache(instance.product)


@receiver(post_save, sender=ProductImage)
@receiver(post_delete, sender=ProductImage)
def product_image_changed(sender, instance, **kwargs):
    _invalidate_product_cache(instance.product)


@receiver(m2m_changed, sender=ProductVariant.attributes.through)
def variant_attributes_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        _invalidate_product_cache(instance.product)


# Simple prefix-based invalidation (best-effort) - scans cache backend if supported
PREFIXES = [
    'ProductViewSet', 'PopularProductViewSet', 'NewArrivalProductViewSet'
]


def _invalidate_product_cache(product: Product):
    try:
        cache_backend = cache
        base_key_prefix = getattr(cache_backend, 'key_prefix', '')
        if hasattr(cache_backend, 'client') and hasattr(cache_backend.client, 'get_client'):
            client = cache_backend.client.get_client(write=True)
            for cls_name in PREFIXES:
                pattern = f"{base_key_prefix}:public:{cls_name}:*" if base_key_prefix else f"public:{cls_name}:*"
                for key in client.scan_iter(match=pattern):
                    client.delete(key)
        else:
            for cls_name in PREFIXES:
                retrieve_key = f"public:{cls_name}:retrieve:{product.slug}"
                cache.delete(retrieve_key)
    except Exception:
        pass
