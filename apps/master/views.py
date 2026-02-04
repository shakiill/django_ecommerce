from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.utils import timezone

from apps.master.models import Supplier  # Supplier imported for new views
from apps.user.models import Staff



@staff_member_required(login_url='staff_login')
def attribute_page(request):
    """
    Render Brands list page.
    """
    return render(request, "master/attribute_list.html", {})

@staff_member_required(login_url='staff_login')
def brand_page(request):
    """
    Render Brands list page.
    """
    return render(request, "master/brand_list.html", {})


@staff_member_required(login_url='staff_login')
def tag_page(request):
    return render(request, "master/tag_list.html", {})

# Replace simple supplier_page with a full list view and add create/edit endpoints below

@staff_member_required(login_url='staff_login')
def supplier_list(request):
    """
    Supplier listing page. Template may fetch dynamic content or render context.
    """
    suppliers = Supplier.objects.all().order_by('-created_at')
    return render(request, "master/supplier_list.html", {'suppliers': suppliers})


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        # include core fields; templates can hide/show as needed
        fields = [
            'contact_type', 'business_name', 'prefix', 'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'mobile', 'alternate_contact_number', 'landline', 'email',
            'tax_number', 'opening_balance', 'pay_term', 'pay_term_type',
            'address_line1', 'address_line2', 'city', 'state', 'country', 'zip_code', 'shipping_address',
            'assigned_to',
            'custom_field_1','custom_field_2','custom_field_3','custom_field_4','custom_field_5',
            'custom_field_6','custom_field_7','custom_field_8','custom_field_9','custom_field_10',
            'is_active','notes'
        ]
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows':3}),
            'address_line1': forms.Textarea(attrs={'rows':2}),
            'notes': forms.Textarea(attrs={'rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super(SupplierForm, self).__init__(*args, **kwargs)
        # limit assigned_to choices to active staff
        self.fields['assigned_to'].queryset = Staff.objects.filter(is_active=True)
        self.fields['assigned_to'].required = False

        # Apply Metronic / Bootstrap 5 styles across widgets
        for name, field in self.fields.items():
            widget = field.widget

            # Boolean checkbox
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
                continue

            # Textarea
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'form-control form-control-solid form-control-sm')
                continue

            # Multiple select (ManyToMany) - add select2 class
            if isinstance(widget, forms.SelectMultiple):
                widget.attrs.setdefault('class', 'form-select form-select-solid form-select-sm select2')
                widget.attrs.setdefault('data-placeholder', 'Select multiple...')
                continue

            # Single select (ForeignKey or choices) - add select2 class
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault('class', 'form-select form-select-solid form-select-sm select2')
                widget.attrs.setdefault('data-placeholder', 'Choose an option...')
                continue

            # Date input fields
            if 'date' in name or 'dob' in name or isinstance(widget, forms.DateInput):
                widget.input_type = 'date'
                widget.attrs.setdefault('class', 'form-control form-control-solid form-control-sm')
                continue

            # Default: text-like inputs
            widget.attrs.setdefault('class', 'form-control form-control-solid form-control-sm')

    def clean(self):
        cleaned_data = super().clean()
        contact_type = cleaned_data.get('contact_type')
        business_name = cleaned_data.get('business_name')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        errors = {}
        if contact_type == Supplier.Type.BUSINESS:
            if not business_name:
                errors['business_name'] = 'Business name is required for business type.'
        elif contact_type == Supplier.Type.INDIVIDUAL:
            if not first_name:
                errors['first_name'] = 'First name is required for individual type.'
            if not last_name:
                errors['last_name'] = 'Last name is required for individual type.'
        if errors:
            from django.core.exceptions import ValidationError
            raise ValidationError(errors)
        return cleaned_data


@staff_member_required(login_url='staff_login')
def supplier_create(request):
    """
    Create supplier. Supports normal POST (redirect) and AJAX POST (returns JSON).
    """
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES)
        if form.is_valid():
            supplier = form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': supplier.id, 'display': supplier.get_display_name()})
            # changed: use non-namespaced URL name
            return redirect('supplier_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = SupplierForm()
    return render(request, "master/supplier_form.html", {'form': form, 'is_edit': False})


@staff_member_required(login_url='staff_login')
def supplier_edit(request, pk):
    """
    Edit supplier. Supports AJAX similar to create.
    """
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': supplier.id, 'display': supplier.get_display_name()})
            # changed: use non-namespaced URL name
            return redirect('supplier_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = SupplierForm(instance=supplier)
    return render(request, "master/supplier_form.html", {'form': form, 'is_edit': True, 'supplier': supplier})


@staff_member_required(login_url='staff_login')
def supplier_view(request, pk):
    """
    Return full supplier data as JSON for modal/detail view.
    """
    supplier = get_object_or_404(Supplier, pk=pk)
    data = {
        'id': supplier.id,
        'contact_type': supplier.get_contact_type_display(),
        'contact_id': supplier.contact_id,
        'display_name': supplier.get_display_name(),
        'business_name': supplier.business_name,
        'prefix': supplier.prefix,
        'first_name': supplier.first_name,
        'middle_name': supplier.middle_name,
        'last_name': supplier.last_name,
        'date_of_birth': supplier.date_of_birth.isoformat() if supplier.date_of_birth else None,
        'mobile': supplier.mobile,
        'alternate_contact_number': supplier.alternate_contact_number,
        'landline': supplier.landline,
        'email': supplier.email,
        'tax_number': supplier.tax_number,
        'opening_balance': str(supplier.opening_balance) if supplier.opening_balance is not None else None,
        'pay_term': supplier.pay_term,
        'pay_term_type': supplier.pay_term_type,
        'address_line1': supplier.address_line1,
        'address_line2': supplier.address_line2,
        'city': supplier.city,
        'state': supplier.state,
        'country': supplier.country,
        'zip_code': supplier.zip_code,
        'shipping_address': supplier.shipping_address,
        'assigned_to': [{'id': s.id, 'name': s.get_display_name()} for s in supplier.assigned_to.all()],
        'custom_fields': {
            'custom_field_1': supplier.custom_field_1,
            'custom_field_2': supplier.custom_field_2,
            'custom_field_3': supplier.custom_field_3,
            'custom_field_4': supplier.custom_field_4,
            'custom_field_5': supplier.custom_field_5,
            'custom_field_6': supplier.custom_field_6,
            'custom_field_7': supplier.custom_field_7,
            'custom_field_8': supplier.custom_field_8,
            'custom_field_9': supplier.custom_field_9,
            'custom_field_10': supplier.custom_field_10,
        },
        'is_active': supplier.is_active,
        'notes': supplier.notes,
        'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
        'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
    }
    return JsonResponse(data)


@staff_member_required(login_url='staff_login')
def supplier_staff_list(request):
    """
    Return active staff list as JSON for dynamic selects/autocomplete.
    """
    staff_qs = Staff.objects.filter(is_active=True).order_by('name')[:200]
    data = [{'id': s.id, 'name': s.get_display_name(), 'username': s.username} for s in staff_qs]
    return JsonResponse({'results': data})


@staff_member_required(login_url='staff_login')
def tax_page(request):
    return render(request, "master/tax_list.html", {})

@staff_member_required(login_url='staff_login')
def unit_page(request):
    return render(request, "master/unit_list.html", {})

@staff_member_required(login_url='staff_login')
def category_page(request):
    return render(request, "master/category_list.html", {})

@staff_member_required(login_url='staff_login')
def warehouse_page(request):
    return render(request, "master/warehouse_list.html", {})

@staff_member_required(login_url='staff_login')
def currency_page(request):
    return render(request, "master/currency_list.html", {})

@staff_member_required(login_url='staff_login')
def paymentmethod_page(request):
    return render(request, "master/paymentmethod_list.html", {})

@staff_member_required(login_url='staff_login')
def shippingmethod_page(request):
    return render(request, "master/shippingmethod_list.html", {})
