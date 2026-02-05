"""
Customer-facing storefront views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class StorefrontHomeView(TemplateView):
    """
    Homepage with hero slider, featured products, new arrivals.
    All data loaded via AJAX from APIs.
    """
    template_name = 'storefront/home.html'


class ProductListView(TemplateView):
    """
    Product listing page with AJAX filtering, search, and sorting.
    """
    template_name = 'storefront/product_list.html'


from django.shortcuts import get_object_or_404
from apps.ecom.models import Product

class ProductDetailView(TemplateView):
    """
    Product detail page with variant selection and add to cart.
    Product data loaded via AJAX using slug from URL.
    """
    template_name = 'storefront/product_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=slug, is_active=True)
        context['product'] = product
        
        # Prepare variants data for frontend
        variants = product.variants.filter(is_active=True).select_related('product').prefetch_related('attributes__attribute')
        
        # 1. Collect all available attributes (e.g. Color: [Red, Blue], Size: [S, M])
        # Structure: { 'Color': { 'id': 1, 'values': [{'id': 10, 'value': 'Red', 'code': '#ff0000'}, ...] } }
        available_attributes = {}
        
        # 2. Build variant map for easy lookup by attributes
        # Structure: { '10-20': { 'id': 1, 'price': 100, 'sku': '...', 'stock': 10 } } (where 10, 20 are attribute value IDs)
        variant_map = {}
        
        for variant in variants:
            # Create a sorted key of attribute value IDs to uniquely identify this variant configuration
            # e.g., "10-25" (ColorID-SizeID)
            attr_values = variant.attributes.all()
            if not attr_values:
                continue
                
            attr_key_parts = []
            for val in attr_values:
                attr_name = val.attribute.name
                
                if attr_name not in available_attributes:
                    available_attributes[attr_name] = {
                        'name': attr_name,
                        'id': val.attribute.id,
                        'values': []
                    }
                
                # Add value if not present
                existing_ids = [v['id'] for v in available_attributes[attr_name]['values']]
                if val.id not in existing_ids:
                    available_attributes[attr_name]['values'].append({
                        'id': val.id, 
                        'value': val.value, 
                        'color_code': val.color_code
                    })
                
                attr_key_parts.append(val.id)
            
            # Sort IDs to ensure consistent key generation regardless of DB return order
            attr_key_parts.sort()
            attr_key = "-".join(map(str, attr_key_parts))
            
            variant_map[attr_key] = {
                'id': variant.id,
                'price': float(variant.get_effective_price()),
                'old_price': float(variant.price) if variant.is_on_sale else None,
                'sku': variant.sku,
                'stock': variant.get_total_stock(),
                'image': variant.image.url if variant.image else None
            }

        # Pre-select default variant attributes
        default_variant_value_ids = []
        if product.default_variant:
            default_variant_value_ids = list(product.default_variant.attributes.values_list('id', flat=True))
        
        import json
        context['available_attributes'] = json.dumps(available_attributes)
        context['variant_map'] = json.dumps(variant_map)
        context['default_variant_value_ids'] = default_variant_value_ids
        return context


class CartView(LoginRequiredMixin, TemplateView):
    """
    Shopping cart page with AJAX operations.
    """
    template_name = 'storefront/cart.html'
    login_url = '/user/login/'


class CheckoutView(LoginRequiredMixin, TemplateView):
    """
    Multi-step checkout process.
    """
    template_name = 'storefront/checkout.html'
    login_url = '/user/login/'


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Customer dashboard overview.
    """
    template_name = 'storefront/dashboard/overview.html'
    login_url = '/user/login/'


class OrderHistoryView(LoginRequiredMixin, TemplateView):
    """
    Customer order history.
    """
    template_name = 'storefront/dashboard/orders.html'
    login_url = '/user/login/'


class OrderDetailView(LoginRequiredMixin, TemplateView):
    """
    Customer order detail.
    """
    template_name = 'storefront/dashboard/order_detail.html'
    login_url = '/user/login/'


class AddressManagementView(LoginRequiredMixin, TemplateView):
    """
    Customer address management.
    """
    template_name = 'storefront/dashboard/addresses.html'
    login_url = '/user/login/'


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Customer profile settings.
    """
    template_name = 'storefront/dashboard/profile.html'
    login_url = '/user/login/'


class CustomerRegisterView(TemplateView):
    """
    Customer registration page.
    """
    template_name = 'storefront/register.html'
