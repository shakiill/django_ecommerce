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


class ProductDetailView(TemplateView):
    """
    Product detail page with variant selection and add to cart.
    Product data loaded via AJAX using slug from URL.
    """
    template_name = 'storefront/product_detail.html'


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
