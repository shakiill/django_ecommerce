# views.py

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from .forms import ProductForm
from .models import ProductVariant, Product
from ..master.models import Attribute, Category, Brand, AttributeValue, Unit, Tax


class ProductListView(TemplateView):
    template_name = 'product/products.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['brands'] = Brand.objects.filter(is_active=True)
        return context


@csrf_exempt
def product_list_ajax(request):
    # DataTables server-side processing
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()

    # Filters
    filter_name = request.GET.get('name', '').strip()
    filter_category = request.GET.get('category', '').strip()
    filter_brand = request.GET.get('brand', '').strip()
    filter_status = request.GET.get('status', '').strip()

    qs = Product.objects.select_related('category', 'brand', 'default_variant')

    # Filtering
    if search_value:
        qs = qs.filter(Q(name__icontains=search_value) | Q(default_variant__sku__icontains=search_value))
    if filter_name:
        qs = qs.filter(name__icontains=filter_name)
    if filter_category:
        qs = qs.filter(category_id=filter_category)
    if filter_brand:
        qs = qs.filter(brand_id=filter_brand)
    if filter_status:
        if filter_status == 'active':
            qs = qs.filter(is_active=True)
        elif filter_status == 'inactive':
            qs = qs.filter(is_active=False)

    total_count = qs.count()
    qs = qs.order_by('-created_at')[start:start + length]

    data = []
    for product in qs:
        data.append({
            'thumbnail': f'<img src="{product.thumbnail.url if product.thumbnail else ""}" style="height:40px;width:auto;">' if product.thumbnail else '',
            'name': product.name,
            'category': product.category.name if product.category else '',
            'brand': product.brand.name if product.brand else '',
            'total_stock': product.get_total_stock() if product.track_inventory else '∞',
            'default_price': str(product.get_price()),
            'status': '<span class="badge bg-success">Active</span>' if product.is_active else '<span class="badge bg-secondary">Inactive</span>',
            'created': product.created_at.strftime('%Y-%m-%d'),
            'actions': f'''
                <a href="/product/{product.id}/edit-step1/" class="btn btn-sm btn-primary">Edit</a>
                <a href="/product/{product.id}/variants/" class="btn btn-sm btn-info">Variants</a>
                <a href="/product/{product.id}/images/" class="btn btn-sm btn-instagram">images</a>
            '''
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_count,
        'recordsFiltered': total_count,
        'data': data,
    })


# Add a small helper to normalize boolean-like POST values
def to_bool(val):
    return str(val).lower() in ('1', 'true', 'on', 'yes') if val is not None else False


class ProductCreateView(View):
    def get(self, request):
        form = ProductForm()
        categories = Category.objects.filter(is_active=True)
        brands = Brand.objects.filter(is_active=True)
        attributes = Attribute.objects.filter(is_active=True)
        units = Unit.objects.filter(is_active=True)

        context = {
            'form': form,
            'categories': categories,
            'brands': brands,
            'attributes': attributes,
            'units': units,
            'product': None,  # Add this line so the template can use {{ product }}
        }
        return render(request, 'product/add.html', context)

    def post(self, request):
        # Step 1: General Information + Main Image only
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description')
        # add key_features
        key_features = request.POST.get('key_features', '')
        unit_id = request.POST.get('unit')
        warranty = request.POST.get('warranty', '')
        is_featured = to_bool(request.POST.get('is_featured'))
        meta_title = request.POST.get('meta_title', '')
        meta_description = request.POST.get('meta_description', '')
        # Use helper to parse checkbox value properly
        is_active = to_bool(request.POST.get('is_active'))
        try:
            min_order_quantity = int(request.POST.get('min_order_quantity', 1))
        except (TypeError, ValueError):
            min_order_quantity = 1
        try:
            max_order_quantity = int(request.POST.get('max_order_quantity', 100))
        except (TypeError, ValueError):
            max_order_quantity = 100
        # Add track_inventory and allow_backorder (use helper)
        track_inventory = to_bool(request.POST.get('track_inventory'))
        allow_backorder = to_bool(request.POST.get('allow_backorder'))

        category = Category.objects.get(id=category_id) if category_id else None
        brand = Brand.objects.get(id=brand_id) if brand_id else None
        unit = None
        if unit_id:
            from apps.master.models import Unit
            unit = Unit.objects.get(id=unit_id)

        thumb_image = request.FILES.get('thumbnail')
        thumbnail_hover = request.FILES.get('thumbnail_hover')

        product = Product.objects.create(
            name=name,
            slug=slug,
            category=category,
            brand=brand,
            description=description,
            key_features=key_features,
            unit=unit,
            warranty=warranty,
            is_featured=is_featured,
            meta_title=meta_title,
            meta_description=meta_description,
            is_active=is_active,
            is_variant=False,
            thumbnail=thumb_image,
            thumbnail_hover=thumbnail_hover,
            min_order_quantity=min_order_quantity,
            max_order_quantity=max_order_quantity,
            track_inventory=track_inventory,
            allow_backorder=allow_backorder,
        )

        # No multiple images, only thumb_image is handled

        # Redirect to Step 2: Variants & Warehouse
        return redirect('product_variants_step', product_id=product.id)


class ProductStep1EditView(View):
    """
    Edit Step 1 (General Information) for an existing product.
    Reuses product_create.html in edit mode.
    """

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        form = ProductForm(instance=product)
        categories = Category.objects.filter(is_active=True)
        brands = Brand.objects.filter(is_active=True)
        attributes = Attribute.objects.filter(is_active=True)
        units = Unit.objects.filter(is_active=True)
        context = {
            'form': form,
            'categories': categories,
            'brands': brands,
            'attributes': attributes,
            'product': product,
            'units': units,
        }
        return render(request, 'product/add.html', context)

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        # Read posted fields
        name = request.POST.get('name') or product.name
        slug = request.POST.get('slug') or product.slug
        category_id = request.POST.get('category')
        brand_id = request.POST.get('brand')
        description = request.POST.get('description', product.description)
        key_features = request.POST.get('key_features', product.key_features)
        unit_id = request.POST.get('unit')
        warranty = request.POST.get('warranty', product.warranty or '')
        is_featured = to_bool(request.POST.get('is_featured'))
        meta_title = request.POST.get('meta_title', product.meta_title or '')
        meta_description = request.POST.get('meta_description', product.meta_description or '')
        # Use helper to parse is_active correctly
        is_active = to_bool(request.POST.get('is_active'))
        try:
            min_order_quantity = int(request.POST.get('min_order_quantity', product.min_order_quantity))
        except (TypeError, ValueError):
            min_order_quantity = product.min_order_quantity
        try:
            max_order_quantity = int(request.POST.get('max_order_quantity', product.max_order_quantity))
        except (TypeError, ValueError):
            max_order_quantity = product.max_order_quantity

        # Add track_inventory and allow_backorder (use helper)
        track_inventory = to_bool(request.POST.get('track_inventory'))
        allow_backorder = to_bool(request.POST.get('allow_backorder'))

        category = Category.objects.get(id=category_id) if category_id else None
        brand = Brand.objects.get(id=brand_id) if brand_id else None
        unit = None
        if unit_id:
            from apps.master.models import Unit
            unit = Unit.objects.get(id=unit_id)
        new_thumb = request.FILES.get('thumbnail')
        new_thumbnail_hover = request.FILES.get('thumbnail_hover')

        # Apply updates
        product.name = name
        product.slug = slug
        product.category = category
        product.brand = brand
        product.description = description
        product.key_features = key_features
        product.unit = unit
        product.warranty = warranty
        product.is_featured = is_featured
        product.meta_title = meta_title
        product.meta_description = meta_description
        product.is_active = is_active
        product.min_order_quantity = min_order_quantity
        product.max_order_quantity = max_order_quantity
        product.track_inventory = track_inventory
        product.allow_backorder = allow_backorder
        if new_thumb:
            product.thumbnail = new_thumb
        if new_thumbnail_hover:
            product.thumbnail_hover = new_thumbnail_hover

        product.save()

        # Continue to Step 2 (Variants)
        return redirect('product_variants_step', product_id=product.id)


class ProductVariantWarehouseView(View):
    """
    Step 2: Manage Variants
    """

    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        attributes = Attribute.objects.filter(is_active=True)
        taxes = Tax.objects.filter(is_active=True)

        # Build existing variants payload for rendering/editing
        existing_variants = []
        for v in product.variants.all().prefetch_related('attributes'):
            avs = list(v.attributes.all()[:2])
            first_attr_id = avs[0].id if len(avs) > 0 else ''
            second_attr_id = avs[1].id if len(avs) > 1 else ''
            combo = " / ".join([a.value for a in avs]) if avs else ''
            existing_variants.append({
                'id': v.id,
                'sku': v.sku,
                'purchase_price': v.purchase_price,
                'price': v.price,
                'is_active': v.is_active,
                'first_attr_id': first_attr_id,
                'second_attr_id': second_attr_id,
                'combination': combo,
                'is_default': (product.default_variant_id == v.id),
            })

        # NEW: determine which attributes and values were used across existing variants
        attr_values_by_attr = {}
        for v in product.variants.all().prefetch_related('attributes'):
            for av in v.attributes.all():
                attr_values_by_attr.setdefault(av.attribute_id, set()).add(av.id)

        attr_ids = list(attr_values_by_attr.keys())
        pre_first_attr_id = attr_ids[0] if len(attr_ids) > 0 else None
        pre_second_attr_id = attr_ids[1] if len(attr_ids) > 1 else None
        pre_first_value_ids = list(attr_values_by_attr.get(pre_first_attr_id, [])) if pre_first_attr_id else []
        pre_second_value_ids = list(attr_values_by_attr.get(pre_second_attr_id, [])) if pre_second_attr_id else []

        context = {
            'product': product,
            'attributes': attributes,
            'taxes': taxes,
            'existing_variants': existing_variants,
            # NEW: pass preselected attribute/value IDs for UI auto-check
            'preselected_first_attribute_id': pre_first_attr_id,
            'preselected_second_attribute_id': pre_second_attr_id,
            'preselected_first_value_ids': pre_first_value_ids,
            'preselected_second_value_ids': pre_second_value_ids,
        }
        return render(request, 'product/variants.html', context)

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        has_variants = to_bool(request.POST.get('has_variants'))
        errors = []

        # Update product-level tax/margin settings
        product.profit_margin = request.POST.get('profit_margin', product.profit_margin)
        product.tax_type = request.POST.get('tax_type', product.tax_type)
        selling_tax_id = request.POST.get('selling_tax')
        if selling_tax_id:
            product.selling_tax = get_object_or_404(Tax, id=selling_tax_id)
        else:
            product.selling_tax = None
        product.save()

        if not has_variants:
            single_sku = request.POST.get('single_sku')
            single_price = request.POST.get('single_price')
            single_purchase_price = request.POST.get('single_purchase_price')
            single_is_active = True
            single_image = request.FILES.get('single_image')

            # Validate
            try:
                single_price_val = float(single_price) if single_price is not None and single_price != '' else None
            except (TypeError, ValueError):
                single_price_val = None
                errors.append('Invalid price for single product.')

            try:
                single_purchase_price_val = float(single_purchase_price) if single_purchase_price is not None and single_purchase_price != '' else None
            except (TypeError, ValueError):
                single_purchase_price_val = None

            if not single_sku or single_price_val is None:
                errors.append('SKU and Price are required for the single product.')

            if errors:
                for e in errors:
                    messages.error(request, e)
                return redirect('product_variants_step', product_id=product.id)

            # Update or create single default variant; delete others
            variant = product.default_variant
            if variant:
                variant.sku = single_sku
                # Always update price and purchase_price, even if 0 or blank
                variant.price = single_price_val
                variant.purchase_price = single_purchase_price_val
                variant.is_active = single_is_active
                if single_image:
                    variant.image = single_image
                variant.attributes.clear()  # ensure no variation attributes for single mode
                variant.save()
                product.variants.exclude(id=variant.id).delete()
            else:
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=single_sku,
                    price=single_price_val,
                    purchase_price=single_purchase_price_val,
                    is_active=single_is_active,
                    image=single_image
                )
                # ensure no attributes for single mode
                variant.attributes.clear()

            product.is_variant = False
            product.default_variant = variant
            product.save(update_fields=['is_variant', 'default_variant'])

        else:
            # Multiple variants (upsert)
            default_index = request.POST.get('default_variant')
            index = 0
            rows_found = 0

            # Gather for validation (required, duplicate SKU check)
            seen_skus = set()
            while f'variants[{index}][sku]' in request.POST:
                sku = (request.POST.get(f'variants[{index}][sku]') or '').strip()
                price_raw = request.POST.get(f'variants[{index}][price]')
                try:
                    price_val = float(price_raw) if price_raw is not None and price_raw != '' else None
                except (TypeError, ValueError):
                    price_val = None

                if not sku or price_val is None:
                    errors.append(f'Row {index + 1}: SKU and Price are required.')
                if sku:
                    if sku in seen_skus:
                        errors.append(f'Row {index + 1}: Duplicate SKU "{sku}".')
                    else:
                        seen_skus.add(sku)

                rows_found += 1
                index += 1

            if rows_found == 0:
                errors.append('Please generate at least one variant.')

            # Require selecting a default variant
            if default_index is None or not f'variants[{default_index}][sku]' in request.POST:
                errors.append('Please select one default variant.')

            if errors:
                for e in errors:
                    messages.error(request, e)
                return redirect('product_variants_step', product_id=product.id)

            # Upsert submitted variants
            index = 0
            kept_ids = []
            default_variant_obj = None

            while f'variants[{index}][sku]' in request.POST:
                vid = request.POST.get(f'variants[{index}][id]')
                sku = (request.POST.get(f'variants[{index}][sku]') or '').strip()
                price_raw = request.POST.get(f'variants[{index}][price]')
                try:
                    price = float(price_raw) if price_raw is not None and price_raw != '' else None
                except (TypeError, ValueError):
                    price = None

                purchase_price_raw = request.POST.get(f'variants[{index}][purchase_price]')
                try:
                    purchase_price = float(purchase_price_raw) if purchase_price_raw is not None and purchase_price_raw != '' else None
                except (TypeError, ValueError):
                    purchase_price = None

                is_variant_active = to_bool(request.POST.get(f'variants[{index}][is_active]'))
                first_attr_id = request.POST.get(f'variants[{index}][first_attr_id]')
                second_attr_id = request.POST.get(f'variants[{index}][second_attr_id]')
                # variant_image = request.FILES.get(f'variants[{index}][image]')  # removed

                if vid:
                    variant = get_object_or_404(ProductVariant, id=vid, product=product)
                    variant.sku = sku
                    variant.price = price
                    variant.purchase_price = purchase_price
                    variant.is_active = is_variant_active
                    # if variant_image:
                    #     variant.image = variant_image  # removed
                    variant.attributes.clear()
                else:
                    variant = ProductVariant.objects.create(
                        product=product,
                        sku=sku,
                        price=price,
                        purchase_price=purchase_price,
                        is_active=is_variant_active,
                        # image=variant_image  # removed
                    )

                if first_attr_id:
                    variant.attributes.add(AttributeValue.objects.get(id=first_attr_id))
                if second_attr_id:
                    variant.attributes.add(AttributeValue.objects.get(id=second_attr_id))

                variant.save()
                kept_ids.append(variant.id)
                if str(index) == str(default_index):
                    default_variant_obj = variant

                index += 1

            product.variants.exclude(id__in=kept_ids).delete()

            product.is_variant = True
            if default_variant_obj:
                product.default_variant = default_variant_obj
                product.save(update_fields=['is_variant', 'default_variant'])
            else:
                product.save(update_fields=['is_variant'])

        return redirect('product_list')


def get_attribute_values(request):
    """AJAX endpoint to get attribute values for selected attributes"""
    attribute_ids = request.GET.get('attribute_ids', '')
    if attribute_ids:
        ids = [int(id) for id in attribute_ids.split(',') if id.strip()]
        attributes = Attribute.objects.filter(id__in=ids).prefetch_related('values')

        data = []
        for attribute in attributes:
            values = attribute.values.all()
            value_list = []
            for v in values:
                value_data = {
                    'id': v.id,
                    'value': v.value
                }
                if v.color_code:
                    value_data['color_code'] = v.color_code
                value_list.append(value_data)

            data.append({
                'attribute': {'id': attribute.id, 'name': attribute.name},
                'values': value_list
            })
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse([], safe=False)
