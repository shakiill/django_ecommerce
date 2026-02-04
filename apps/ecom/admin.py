from django.contrib import admin
from django.utils.html import format_html

from apps.ecom.models import Product, ProductVariant, ProductImage
from apps.order.models import Cart, CartItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'display_order', 'alt_text']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    show_change_link = True
    fields = ['sku', 'variant_name', 'price', 'stock', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'thumbnail_preview', 'is_variant', 'category', 'brand', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'category__name', 'brand__name']
    list_filter = ['is_active', 'is_featured', 'category', 'brand', 'created_at']
    inlines = [ProductImageInline, ProductVariantInline]
    prepopulated_fields = {'slug': ('name',)}

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = "Thumbnail"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'sku', 'variant_name', 'price', 'stock', 'is_active']
    search_fields = ['sku', 'product__name', 'variant_name']
    list_filter = ['is_active', 'product__category', 'product__brand']
    autocomplete_fields = ['product']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'display_order', 'created_at']
    list_filter = ['product__category', 'product__brand']
    search_fields = ['product__name', 'alt_text']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    inlines = [CartItemInline]
