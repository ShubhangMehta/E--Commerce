from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from orders.services.order_service import OrderService
from orders.models import Order
from users.models import Coordinate,SubjectMember
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from users.views.theme_views import get_subject_member
# import cart helpers from THEMES
from themes.views import _get_cart, _set_cart, _cart_items_and_totals, _theme_path


@login_required
def checkout_view(request):
    cart_data = _get_cart(request.session)
    cart_items, cart_subtotal, cart_total = _cart_items_and_totals(cart_data)

    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("product_list")

    # ⭐ get tenant user the SAME WAY whole project does
    subject = get_subject_member(request)

    # load addresses correctly
    addresses = Coordinate.objects.filter(user=subject)

    if request.method == "POST":
        address_id = request.POST.get("address_id")

        

        order = OrderService.create_order_from_cart(
            tenant=request.tenant,
            subject=subject,
            cart_items=cart_items,
            address_id=address_id,
        )

        _set_cart(request.session, {})

        return redirect("orders_storefront:order_success", order_id=order.id)

    return render(request, _theme_path(request, "checkout.html"), {
        "cart_items": cart_items,
        "cart_total": cart_total,
        "addresses": addresses,
    })

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        subject = get_subject_member(request)
    )

    return render(request, _theme_path(request, "order_success.html"), {
        "order": order
    })
@login_required
def my_orders_view(request):
    orders = Order.objects.filter(
        subject=get_subject_member(request)

    ).order_by("-created_at")

    return render(request, _theme_path(request, "previous_order_listing.html"), {
        "orders": orders
    })

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        subject = get_subject_member(request)
    )

    items = order.items.all()

    return render(
        request, _theme_path(request, "cust_order_detail.html"),
        {
            "order": order,
            "items": items,
        }
    )





@login_required
def invoice_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        subject = get_subject_member(request)
    )
    items = order.items.all()

    return render(
        request,
         _theme_path(request, "cust_invoice.html"),  # fixed path
        {
            "order": order,
            "items": items,
        }
    )


@login_required
def invoice_pdf_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        subject = get_subject_member(request)
    )
    items = order.items.all()

    template = get_template("themes/default/cust_invoice.html")  # fixed path
    html = template.render({
        "order": order,
        "items": items,
        "request": request,  # for static/media URLs
    })

    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    if pdf.err:
        return HttpResponse("Error generating PDF")

    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{order.id}.pdf"'
    return response
