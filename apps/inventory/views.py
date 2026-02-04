from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.ecom.models import Product, ProductVariant
from apps.inventory.forms import (
    PurchaseRequisitionForm,
    PurchaseRequisitionItemFormSet,
)
from apps.inventory.forms_po import PurchaseOrderForm, PurchaseOrderItemFormSet, AdditionalCostFormSet
from apps.inventory.models import PurchaseRequisition, PurchaseOrder
from apps.inventory.requisitions import generate_pr_number, recalc_requisition_total
from apps.inventory.pos import generate_po_number, recalc_po_totals, update_requisition_ordered
from apps.master.models import Warehouse, Supplier, Tax


@staff_member_required(login_url='staff_login')
@require_GET
def requisition_list(request):
    context = {
        'requisition_statuses': PurchaseRequisition.STATUS_CHOICES,
        'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
    }
    return render(request, 'inventory/requisition.html', context)


@staff_member_required(login_url='staff_login')
@require_GET
def requisition_list_data(request):
    qs = PurchaseRequisition.objects.select_related('warehouse', 'requested_by').all()

    # Filtering
    status = request.GET.get('status')
    warehouse = request.GET.get('warehouse')
    pr_number = request.GET.get('pr_number')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        qs = qs.filter(status=status)
    if warehouse:
        qs = qs.filter(warehouse_id=warehouse)
    if pr_number:
        qs = qs.filter(pr_number__icontains=pr_number)
    if date_from:
        qs = qs.filter(requisition_date__gte=date_from)
    if date_to:
        qs = qs.filter(requisition_date__lte=date_to)

    data = []
    for pr in qs[:1000]:  # safety cap
        full_name = getattr(pr.requested_by, 'get_full_name', None)
        requested_by = full_name() if callable(full_name) and full_name() else str(pr.requested_by)
        data.append({
            'id': pr.id,
            'pr_number': pr.pr_number,
            'warehouse': getattr(pr.warehouse, 'name', ''),
            'requisition_date': pr.requisition_date.strftime('%Y-%m-%d') if pr.requisition_date else '',
            'required_date': pr.required_date.strftime('%Y-%m-%d') if pr.required_date else '',
            'status': pr.get_status_display(),
            'priority': pr.get_priority_display(),
            'requested_by': requested_by,
            'total_amount': f"{pr.total_amount:.2f}",
            'detail_url': reverse('inventory:requisition_detail', args=[pr.pk]),
            'edit_url': reverse('inventory:requisition_edit', args=[pr.pk]),
            'delete_url': reverse('inventory:requisition_delete', args=[pr.pk]),
        })

    return JsonResponse({'data': data})


@staff_member_required(login_url='staff_login')
def requisition_create(request):
    if request.method == 'POST':
        form = PurchaseRequisitionForm(request.POST)
        formset = PurchaseRequisitionItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            requisition = form.save(commit=False)
            requisition.pr_number = generate_pr_number()
            requisition.requested_by = request.user
            requisition.created_by = request.user
            requisition.updated_by = request.user
            requisition.total_amount = Decimal('0.00')
            requisition.save()

            formset.instance = requisition
            items = formset.save(commit=False)
            for item in items:
                item.created_by = request.user
                item.updated_by = request.user
                item.save()
            for deleted in formset.deleted_objects:
                deleted.delete()

            recalc_requisition_total(requisition)

            messages.success(request, 'Requisition created successfully.')
            return redirect('inventory:requisition_detail', pk=requisition.pk)
    else:
        form = PurchaseRequisitionForm()
        formset = PurchaseRequisitionItemFormSet()

    return render(request, 'inventory/requisition_add.html', {
        'form': form,
        'formset': formset,
        'is_edit': False,
    })


@staff_member_required(login_url='staff_login')
def requisition_edit(request, pk: int):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    if request.method == 'POST':
        form = PurchaseRequisitionForm(request.POST, instance=requisition)
        formset = PurchaseRequisitionItemFormSet(request.POST, instance=requisition)
        if form.is_valid() and formset.is_valid():
            requisition = form.save(commit=False)
            requisition.updated_by = request.user
            requisition.save()

            items = formset.save(commit=False)
            for item in items:
                item.updated_by = request.user
                if not item.pk:
                    item.created_by = request.user
                item.save()
            for deleted in formset.deleted_objects:
                deleted.delete()

            recalc_requisition_total(requisition)
            messages.success(request, 'Requisition updated successfully.')
            return redirect('inventory:requisition_detail', pk=requisition.pk)
    else:
        form = PurchaseRequisitionForm(instance=requisition)
        formset = PurchaseRequisitionItemFormSet(instance=requisition)

    return render(request, 'inventory/requisition_add.html', {
        'form': form,
        'formset': formset,
        'is_edit': True,
        'requisition': requisition,
    })


@staff_member_required(login_url='staff_login')
@require_POST
def requisition_delete(request, pk: int):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    requisition.delete()
    messages.success(request, 'Requisition deleted successfully.')
    return redirect('inventory:requisition_list')


@staff_member_required(login_url='staff_login')
@require_GET
def requisition_detail(request, pk: int):
    requisition = get_object_or_404(PurchaseRequisition.objects.select_related('warehouse', 'requested_by'), pk=pk)
    return render(request, 'inventory/requisition_detail.html', {
        'requisition': requisition,
    })


@staff_member_required(login_url='staff_login')
@require_POST
def requisition_status_change(request, pk: int):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    new_status = request.POST.get('status')
    valid_statuses = {choice[0] for choice in PurchaseRequisition.STATUS_CHOICES}
    if new_status not in valid_statuses:
        return JsonResponse({'ok': False, 'error': 'Invalid status'}, status=400)

    old_status = requisition.status
    requisition.status = new_status
    if new_status == 'approved':
        requisition.approved_by = request.user
    requisition.updated_by = request.user
    # Append history entry in-memory
    requisition.log_status_change(old_status, new_status, user=request.user)
    # Persist all relevant fields including status_history
    update_fields = ['status', 'approved_by', 'updated_by', 'status_history']
    requisition.save(update_fields=[f for f in update_fields if hasattr(requisition, f)])

    last_entry = requisition.status_history[-1] if requisition.status_history else None
    return JsonResponse({'ok': True, 'status': requisition.get_status_display(), 'history': last_entry})


@staff_member_required(login_url='staff_login')
@require_GET
def requisition_pdf(request, pk: int):
    requisition = get_object_or_404(PurchaseRequisition.objects.select_related('warehouse', 'requested_by'), pk=pk)
    html = render_to_string('inventory/requisition_pdf.html', {
        'requisition': requisition,
    })

    try:
        from xhtml2pdf import pisa
    except Exception:
        return HttpResponse(html)  # Fallback: show HTML

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{requisition.pr_number}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors while generating PDF')
    return response


# Purchase Order Views
@staff_member_required(login_url='staff_login')
@require_GET
def po_list(request):
    context = {
        'po_statuses': PurchaseOrder.STATUS_CHOICES,
        'suppliers': Supplier.objects.filter(is_active=True).order_by('business_name'),
        'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
    }
    return render(request, 'inventory/po_list.html', context)


@staff_member_required(login_url='staff_login')
@require_GET
def po_list_data(request):
    qs = PurchaseOrder.objects.select_related('supplier', 'warehouse').all()
    status = request.GET.get('status')
    supplier = request.GET.get('supplier')
    po_number = request.GET.get('po_number')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        qs = qs.filter(status=status)
    if supplier:
        qs = qs.filter(supplier_id=supplier)
    if po_number:
        qs = qs.filter(po_number__icontains=po_number)
    if date_from:
        qs = qs.filter(order_date__gte=date_from)
    if date_to:
        qs = qs.filter(order_date__lte=date_to)

    data = []
    for po in qs[:1000]:
        data.append({
            'id': po.id,
            'po_number': po.po_number,
            'supplier': getattr(po.supplier, 'name', ''),
            'warehouse': getattr(po.warehouse, 'name', ''),
            'order_date': po.order_date.strftime('%Y-%m-%d') if po.order_date else '',
            'expected_delivery_date': po.expected_delivery_date.strftime(
                '%Y-%m-%d') if po.expected_delivery_date else '',
            'status': po.get_status_display(),
            'total_amount': f"{po.total_amount:.2f}",
            'detail_url': reverse('inventory:po_detail', args=[po.pk]),
            'edit_url': reverse('inventory:po_edit', args=[po.pk]),
            'delete_url': reverse('inventory:po_delete', args=[po.pk]),
        })
    return JsonResponse({'data': data})


@staff_member_required(login_url='staff_login')
def po_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderItemFormSet(request.POST, prefix='items')
        cost_formset = AdditionalCostFormSet(request.POST, prefix='costs')
        if form.is_valid() and formset.is_valid() and cost_formset.is_valid():
            po = form.save(commit=False)
            po.po_number = generate_po_number()
            po.status = 'draft'
            po.created_by = request.user
            po.updated_by = request.user
            po.subtotal = Decimal('0.00')
            po.tax_amount = Decimal('0.00')
            po.discount_amount = Decimal('0.00')
            po.total_amount = Decimal('0.00')
            po.save()

            formset.instance = po
            items = formset.save(commit=False)
            for item in items:
                item.created_by = request.user
                item.updated_by = request.user
                item.save()
            for deleted in formset.deleted_objects:
                deleted.delete()

            cost_formset.instance = po
            cost_items = cost_formset.save(commit=False)
            for ci in cost_items:
                ci.save()
            for deleted in cost_formset.deleted_objects:
                deleted.delete()

            recalc_po_totals(po)
            if po.requisition:
                update_requisition_ordered(po.requisition)
            messages.success(request, 'Purchase Order created successfully.')
            return redirect('inventory:po_detail', pk=po.pk)
        # on invalid POST fallthrough: ensure taxes in context below
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet(prefix='items')
        cost_formset = AdditionalCostFormSet(prefix='costs')

    return render(request, 'inventory/po_add.html', {
        'form': form,
        'formset': formset,
        'cost_formset': cost_formset,
        'is_edit': False,
        'taxes': Tax.objects.filter(is_active=True).order_by('name'),
    })


@staff_member_required(login_url='staff_login')
def po_edit(request, pk: int):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderItemFormSet(request.POST, instance=po, prefix='items')
        cost_formset = AdditionalCostFormSet(request.POST, instance=po, prefix='costs')
        if form.is_valid() and formset.is_valid() and cost_formset.is_valid():
            po = form.save(commit=False)
            po.updated_by = request.user
            po.save()

            items = formset.save(commit=False)
            for item in items:
                item.updated_by = request.user
                if not item.pk:
                    item.created_by = request.user
                item.save()
            for deleted in formset.deleted_objects:
                deleted.delete()

            cost_items = cost_formset.save(commit=False)
            for ci in cost_items:
                ci.save()
            for deleted in cost_formset.deleted_objects:
                deleted.delete()

            recalc_po_totals(po)
            if po.requisition:
                update_requisition_ordered(po.requisition)
            messages.success(request, 'Purchase Order updated successfully.')
            return redirect('inventory:po_detail', pk=po.pk)
        # on invalid POST fallthrough: ensure taxes in context below
    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderItemFormSet(instance=po, prefix='items')
        cost_formset = AdditionalCostFormSet(instance=po, prefix='costs')

    return render(request, 'inventory/po_add.html', {
        'form': form,
        'formset': formset,
        'cost_formset': cost_formset,
        'is_edit': True,
        'po': po,
        'taxes': Tax.objects.filter(is_active=True).order_by('name'),
    })


@staff_member_required(login_url='staff_login')
@require_POST
def po_delete(request, pk: int):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    po.delete()
    messages.success(request, 'Purchase Order deleted successfully.')
    return redirect('inventory:po_list')


@staff_member_required(login_url='staff_login')
@require_GET
def po_detail(request, pk: int):
    po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'warehouse'), pk=pk)
    return render(request, 'inventory/po_detail.html', {'po': po})


@staff_member_required(login_url='staff_login')
@require_POST
def po_status_change(request, pk: int):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    new_status = request.POST.get('status')
    valid = {c[0] for c in PurchaseOrder.STATUS_CHOICES}
    if new_status not in valid:
        return JsonResponse({'ok': False, 'error': 'Invalid status'}, status=400)

    old_status = po.status
    po.status = new_status
    if new_status == 'confirmed':
        po.approved_by = request.user
    po.updated_by = request.user
    # Append history entry in-memory
    po.log_status_change(old_status, new_status, user=request.user)
    update_fields = ['status', 'approved_by', 'updated_by', 'status_history']
    po.save(update_fields=[f for f in update_fields if hasattr(po, f)])

    last_entry = po.status_history[-1] if po.status_history else None
    return JsonResponse({'ok': True, 'status': po.get_status_display(), 'history': last_entry})


@staff_member_required(login_url='staff_login')
@require_GET
def po_pdf(request, pk: int):
    po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'warehouse'), pk=pk)
    html = render_to_string('inventory/po_pdf.html', {'po': po})

    try:
        from xhtml2pdf import pisa
    except Exception:
        return HttpResponse(html)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{po.po_number}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors while generating PDF')
    return response


# API Endpoints for Bulk Import and Product Search
@staff_member_required(login_url='staff_login')
@require_GET
def api_get_variants(request):
    """
    Get product variants filtered by brand and/or category.
    Used for bulk import functionality.
    """
    try:
        brand_id = request.GET.get('brand')
        category_id = request.GET.get('category')

        variants_qs = ProductVariant.objects.select_related('product', 'product__brand', 'product__category').filter(
            is_active=True,
            product__is_active=True
        )

        if brand_id:
            variants_qs = variants_qs.filter(product__brand_id=brand_id)

        if category_id:
            variants_qs = variants_qs.filter(product__category_id=category_id)

        # Removed hard cap to import ALL variants as requested
        variants = [{
            'id': v.id,
            'display_name': f"{v.product.name} - {v.variant_name} ({v.sku})",
            'sku': v.sku,
            'price': str(v.purchase_price),
            'product_name': v.product.name,
        } for v in variants_qs]

        return JsonResponse({'variants': variants, 'count': len(variants)})
    except Exception as e:
        return JsonResponse({'error': str(e), 'variants': []}, status=500)


@staff_member_required(login_url='staff_login')
@require_GET
def api_search_products(request):
    """
    Search products by name, SKU, or barcode.
    Returns products with variant count.
    """
    try:
        query = request.GET.get('q', '').strip()

        if not query or len(query) < 2:
            return JsonResponse({'products': []})

        # Search in product name or variant SKU/barcode
        products_qs = Product.objects.filter(
            Q(is_active=True) &
            (
                    Q(name__icontains=query) |
                    Q(variants__sku__icontains=query) |
                    Q(variants__barcode__icontains=query)
            )
        ).select_related('brand', 'category').annotate(
            variant_count=Count('variants', filter=Q(variants__is_active=True))
        ).distinct()[:20]

        products = []
        for product in products_qs:
            products.append({
                'id': product.id,
                'name': product.name,
                'brand': product.brand.name if product.brand else '',
                'category': product.category.name if product.category else '',
                'variant_count': product.variant_count,
            })

        return JsonResponse({'products': products})
    except Exception as e:
        return JsonResponse({'error': str(e), 'products': []}, status=500)


@staff_member_required(login_url='staff_login')
@require_GET
def api_get_product_variants(request, product_id):
    """
    Get all variants for a specific product.
    Used when adding all variants of a selected product.
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        variants_qs = product.variants.filter(is_active=True)

        variants = []
        for variant in variants_qs:
            variants.append({
                'id': variant.id,
                'display_name': f"{product.name} - {variant.variant_name} ({variant.sku})",
                'sku': variant.sku,
                'variant_name': variant.variant_name,
                'price': str(variant.price),
                'product_name': product.name,
            })

        return JsonResponse({'variants': variants, 'count': len(variants)})
    except Exception as e:
        return JsonResponse({'error': str(e), 'variants': []}, status=500)


# APIs to support importing from requisition
@staff_member_required(login_url='staff_login')
@require_GET
def api_requisitions_search(request):
    """Search approved or partially ordered PRs by number."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'requisitions': []})
    qs = (PurchaseRequisition.objects
    .filter(pr_number__icontains=q, status__in=['approved', 'partially_ordered', 'ordered'])
    .select_related('warehouse')
    .order_by('-requisition_date')[:20])
    out = [{
        'id': r.id,
        'pr_number': r.pr_number,
        'status': r.status,
        'warehouse': r.warehouse.name if r.warehouse else ''
    } for r in qs]
    return JsonResponse({'requisitions': out})


@staff_member_required(login_url='staff_login')
@require_GET
def api_requisition_outstanding_items(request, requisition_id: int):
    """Return PR items with outstanding quantities (requested - ordered > 0)."""
    pr = get_object_or_404(PurchaseRequisition, pk=requisition_id)
    items = []
    for it in pr.items.select_related('product_variant__product').all():
        outstanding = it.quantity_requested - it.quantity_ordered
        if outstanding > 0:
            items.append({
                'variant_id': it.product_variant_id,
                'sku': it.product_variant.sku,
                'name': f"{it.product_variant.product.name} - {it.product_variant.variant_name}",
                'outstanding_qty': outstanding,
                'suggested_price': str(it.estimated_unit_price),
            })
    return JsonResponse({'items': items})
