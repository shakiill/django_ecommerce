from django import forms
from django.forms import inlineformset_factory

from apps.helpers.forms import SensibleFormset
from apps.inventory.models import PurchaseRequisition, PurchaseRequisitionItem


class PurchaseRequisitionForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisition
        fields = [
            'warehouse', 'requisition_date', 'required_date', 'priority',
            'department', 'purpose', 'notes'
        ]
        widgets = {
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'requisition_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'required_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class PurchaseRequisitionItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequisitionItem
        fields = [
            'product_variant', 'quantity_requested', 'estimated_unit_price',
            'specifications', 'notes'
        ]
        widgets = {
            'product_variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


PurchaseRequisitionItemFormSet = inlineformset_factory(
    parent_model=PurchaseRequisition,
    model=PurchaseRequisitionItem,
    form=PurchaseRequisitionItemForm,
    formset=SensibleFormset,
    fields=['product_variant', 'quantity_requested', 'estimated_unit_price', 'specifications', 'notes'],
    extra=1,
    can_delete=True,
    validate_min=False,
    validate_max=False,
)
