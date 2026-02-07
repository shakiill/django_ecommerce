"""
Customer-facing storefront views.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


from apps.cms.models import HomeSection


class StorefrontHomeView(TemplateView):
    """
    Homepage with hero slider, featured products, new arrivals.
    All data loaded via AJAX from APIs.
    """
    template_name = 'storefront/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch active home sections
        sections = HomeSection.objects.filter(is_active=True).order_by('order')
        context['sections'] = sections
        # Convert to a dictionary for easy access in template: {section_type: True}
        # This allows for {% if home_sections.flash_sale %} style checks
        context['home_sections'] = {s.section_type: True for s in sections}
        return context


class FlashSaleView(TemplateView):
    template_name = 'storefront/flash_sale.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # We can pass any specific data for flash sale here
        return context




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
        context['product_slug'] = self.kwargs.get('slug')
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


class ContactView(TemplateView):
    """
    Public contact page.
    """
    template_name = 'storefront/contact.html'


class WishlistView(LoginRequiredMixin, TemplateView):
    """
    Customer wishlist page.
    """
    template_name = 'storefront/wishlist.html'
    login_url = '/user/login/'

