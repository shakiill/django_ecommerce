from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML
from django import forms
from django_summernote.widgets import SummernoteWidget

from apps.ecom.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'name', 'category', 'brand', 'is_variant', 'is_featured', 'min_order_quantity',
            'max_order_quantity', 'description', 'key_features', 'meta_title', 'meta_description',
            'is_active', 'warranty', 'thumbnail', 'thumbnail_hover', 'unit'
        )
        widgets = {
            'description': SummernoteWidget(),
            'key_features': SummernoteWidget(),
        }
