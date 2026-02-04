from django.contrib import admin

from apps.ecom.models import Product, ProductVariant


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_variant', 'category', 'brand', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']  # fixed: was 'filter', should be 'list_filter'

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'sku', 'price', 'purchase_price', 'is_active']  # show is_active for clarity
    search_fields = ['sku', 'product__name']