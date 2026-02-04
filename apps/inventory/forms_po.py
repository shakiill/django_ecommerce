from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from apps.helpers.forms import SensibleFormset
from apps.inventory.models import PurchaseOrder, PurchaseOrderItem, AdditionalCost


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'requisition', 'supplier', 'warehouse', 'order_date', 'expected_delivery_date', 'shipping_address',
            'payment_method', 'payment_terms', 'shipping_method', 'shipping_cost',
            'notes', 'terms_and_conditions'
        ]
        widgets = {
            'requisition': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shipping_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'shipping_method': forms.Select(attrs={'class': 'form-select'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'product_variant', 'quantity_ordered', 'unit_price', 'discount_percent', 'tax_rate', 'notes'
        ]
        widgets = {
            'product_variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class UniqueVariantPOFormset(SensibleFormset):
    def clean(self):
        super().clean()
        seen = set()
        errors = False
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            variant = form.cleaned_data.get('product_variant')
            if not variant:
                # field-specific errors will handle
                continue
            if variant.pk in seen:
                form.add_error('product_variant', 'Duplicate item. Each product variant can appear only once.')
                errors = True
            else:
                seen.add(variant.pk)
        if errors:
            # Attach a non-form error to indicate duplicates exist
            from django.forms import ValidationError
            raise ValidationError('Duplicate items detected in the Purchase Order. Remove duplicates and try again.')


PurchaseOrderItemFormSet = inlineformset_factory(
    parent_model=PurchaseOrder,
    model=PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    formset=UniqueVariantPOFormset,
    fields=['product_variant', 'quantity_ordered', 'unit_price', 'discount_percent', 'tax_rate', 'notes'],
    extra=1,
    can_delete=True,
    validate_min=False,
    validate_max=False,
)


class AdditionalCostForm(forms.ModelForm):
    class Meta:
        model = AdditionalCost
        fields = ['description', 'amount']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Customs, Insurance'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


AdditionalCostFormSet = inlineformset_factory(
    parent_model=PurchaseOrder,
    model=AdditionalCost,
    form=AdditionalCostForm,
    fields=['description', 'amount'],
    extra=1,
    can_delete=True,
    validate_min=False,
    validate_max=False,
)
