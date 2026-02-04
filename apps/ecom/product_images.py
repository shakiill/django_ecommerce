from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from .models import Product, ProductImage, AttributeValue


@require_http_methods(["GET", "POST"])
def manage_product_images(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)
    # Gather attribute values used in product variants (distinct)
    attr_ids = product.variants.values_list('attributes', flat=True)
    attribute_values = AttributeValue.objects.filter(id__in=attr_ids).distinct()

    if request.method == "POST":
        # Delete single image
        delete_id = request.POST.get("delete_id")
        if delete_id:
            img = get_object_or_404(ProductImage, pk=delete_id, product=product)
            img.delete()
            messages.success(request, "Image deleted.")
            return redirect(request.path)

        # Bulk save
        created = 0
        rows = {}
        # Collect per-index metadata
        for key, val in request.POST.items():
            # Expect keys like images-0-alt_text / images-0-display_order
            if key.startswith("images-"):
                parts = key.split("-")
                if len(parts) >= 3:
                    idx = parts[1]
                    field = parts[2]
                    rows.setdefault(idx, {})[field] = val

        # Collect attribute selections (they are list-based)
        for key in request.POST.keys():
            if key.startswith("images-") and key.endswith("-attributes"):
                idx = key.split("-")[1]
                rows.setdefault(idx, {})["attributes"] = request.POST.getlist(key)

        with transaction.atomic():
            for idx, data in rows.items():
                file_key = f"images-{idx}-image"
                image_file = request.FILES.get(file_key)
                if not image_file:
                    # Skip rows without image (clone rows can be filled later)
                    continue
                alt_text = data.get("alt_text", "")
                display_order_raw = data.get("display_order", "0")
                try:
                    display_order = int(display_order_raw)
                except ValueError:
                    display_order = 0
                obj = ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    alt_text=alt_text,
                    display_order=display_order,
                )
                attr_ids_row = data.get("attributes", [])
                if attr_ids_row:
                    obj.attributes.add(*attr_ids_row)
                created += 1

        if created:
            messages.success(request, f"{created} image(s) uploaded.")
        else:
            messages.warning(request, "No images created (missing files).")
        return redirect(request.path)

    images = product.images.order_by("display_order", "id")
    return render(
        request,
        "product/images.html",
        {
            "product": product,
            "images": images,
            "attribute_values": attribute_values,
        },
    )

# Usage (add to your urls.py):
# path('products/<int:product_id>/images/', manage_product_images, name='product_images')
