from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST
from django.template.loader import render_to_string
from django.utils.http import http_date

import datetime

from .models import Order, OrderStatusLog, OrderStatus, PaymentStatus


# Create your views here.

@require_GET
def order_list(request):
    return render(
        request,
        "order/list.html",
        {
            "order_status_choices": OrderStatus.choices,
            "payment_status_choices": PaymentStatus.choices,
        },
    )


@require_GET
def order_list_data(request):
    draw = int(request.GET.get("draw", "1"))
    start = int(request.GET.get("start", "0"))
    length = int(request.GET.get("length", "10"))

    search_value = request.GET.get("search[value]", "").strip()
    status = request.GET.get("status") or ""
    payment_status = request.GET.get("payment_status") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""
    min_total = request.GET.get("min_total") or ""
    max_total = request.GET.get("max_total") or ""

    qs = Order.objects.select_related("user")
    records_total = qs.count()

    # --- Filters ---
    if status:
        qs = qs.filter(status=status)

    if payment_status:
        qs = qs.filter(payment_status=payment_status)

    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            qs = qs.filter(created_at__date__gte=d_from)

    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            qs = qs.filter(created_at__date__lte=d_to)

    if min_total:
        try:
            qs = qs.filter(total_amount__gte=Decimal(min_total))
        except:
            pass

    if max_total:
        try:
            qs = qs.filter(total_amount__lte=Decimal(max_total))
        except:
            pass

    # --- Search ---
    if search_value:
        qs = qs.filter(
            Q(order_number__icontains=search_value) |
            Q(user__name__icontains=search_value) |
            Q(user__email__icontains=search_value) |
            Q(guest_email__icontains=search_value)
        )

    records_filtered = qs.count()
    page = qs.order_by("-created_at")[start:start + length]

    # --- Response rows ---
    data = []
    for o in page:
        customer = o.user.get_display_name() if o.user else (o.guest_email or "Guest")
        detail_url = reverse("order:order_detail", args=[o.pk])
        data.append({
            "order_number": o.order_number,
            "customer_name": customer,
            "status_display": o.get_status_display(),
            "payment_status_display": o.get_payment_status_display(),
            "total_amount": f"{o.total_amount} {o.currency}",
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
            "actions": f'<a href="{detail_url}" class="btn btn-sm btn-light-primary">View</a>'
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data
    })


def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("user", "shipping_address", "billing_address").prefetch_related("items"),
        pk=pk
    )
    return render(request, "order/detail.html", {
        "order": order,
        "order_status_choices": OrderStatus.choices
    })


@require_POST
def order_status_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get("status")
    valid = {v for v, _ in OrderStatus.choices}
    if new_status not in valid:
        messages.error(request, "Invalid status.")
        return redirect("order:order_detail", pk=pk)
    if order.status == new_status:
        messages.info(request, "Status unchanged.")
        return redirect("order:order_detail", pk=pk)

    old_status = order.status
    order.status = new_status
    # Prevent the post_save signal from creating a duplicate log; we'll create a log with changed_by user
    order._log_skip = True
    order.save(update_fields=["status"])

    # Create explicit log entry with the requesting user
    try:
        OrderStatusLog.objects.create(
            order=order,
            change_type=OrderStatusLog.CHANGE_TYPE_STATUS,
            old_value=old_status or "",
            new_value=new_status or "",
            changed_by=request.user if request.user.is_authenticated else None,
        )
    except Exception:
        # Non-fatal: log creation failure should not break the update flow.
        pass

    messages.success(request, "Status updated.")
    return redirect("order:order_detail", pk=pk)


def order_invoice(request, pk):
    """
    Render a printable invoice for the order and return it as a PDF attachment.
    This endpoint requires WeasyPrint to be installed. If it's not available,
    respond with an error so callers know PDF generation is unavailable.
    """
    order = get_object_or_404(
        Order.objects.select_related("user", "shipping_address", "billing_address")
            .prefetch_related("items", "payments", "status_logs"),
        pk=pk
    )
    context = {"order": order, "generated_at": datetime.datetime.utcnow()}

    # Render invoice HTML
    html_string = render_to_string("order/invoice.html", context, request=request)

    # Require WeasyPrint: produce PDF and return as attachment. Do NOT fall back to HTML.
    try:
        from weasyprint import HTML
    except ImportError:
        # Explicitly inform the caller that server-side PDF generation is not available.
        return HttpResponse(
            "PDF generation is not available on the server. Please install WeasyPrint and its dependencies.",
            status=501,
            content_type="text/plain"
        )

    try:
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"invoice-{order.order_number}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-cache"
        response["Last-Modified"] = http_date()
        return response
    except Exception as exc:
        # If PDF generation fails despite WeasyPrint being present, surface a server error.
        return HttpResponse(
            f"Failed to generate PDF: {str(exc)}",
            status=500,
            content_type="text/plain"
        )
