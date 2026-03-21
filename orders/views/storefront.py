from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa

from orders.models import Order
from users.models import Coordinate, SubjectMember
from orders.services.cart_service import CartService
from orders.services.order_service import OrderService
from users.views.theme_views import get_subject_member

# import theme helpers
from themes.views import _theme_path

@require_http_methods(["GET", "POST"])
def cart_view(request):
    """
    GET: render cart with address selection (right)
    POST: add to cart OR apply coupon OR select address
    """
    # POST actions
    if request.method == "POST":
        # add product
        if request.POST.get("product_id"):
            CartService.add(request.session, request.POST["product_id"], 1)
            messages.success(request, "Added to cart.")
            return redirect("cart")

        # apply coupon
        if "coupon_code" in request.POST:
            CartService.set_coupon(request.session, request.POST.get("coupon_code"))
            messages.success(request, "Coupon updated.")
            return redirect("cart")

        # select address
        if "address_id" in request.POST:
            if not request.user.is_authenticated:
                messages.info(request, "Please login to select address.")
                return redirect("login")
            subject = get_subject_member(request)
            addr_id = request.POST.get("address_id")
            if not Coordinate.objects.filter(user=subject, id=addr_id).exists():
                messages.error(request, "Address not found.")
                return redirect("cart")
            CartService.set_selected_address(request.session, addr_id)
            messages.success(request, "Address selected.")
            return redirect("cart")

    cart_items, cart_subtotal, cart_total = CartService.items_and_totals(request.session)

    addresses = []
    if request.user.is_authenticated:
        subject = get_subject_member(request)
        addresses = Coordinate.objects.filter(user=subject)

    context = {
        "cart_items": cart_items,
        "cart_subtotal": cart_subtotal,
        "cart_total": cart_total,

        # right panel
        "addresses": addresses,
        "selected_address_id": CartService.get_selected_address_id(request.session),

        # coupon
        # "coupon_code": CartService.get_coupon(request.session),

        # you can extend these later:
        "tax_total": 0,
        "discount_total": None,
        "grand_total": cart_total,
    }
    return render(request, _theme_path(request, "cart.html"), context)


@require_http_methods(["POST"])
def cart_update(request):
    CartService.update(request.session, request.POST.get("product_id"), request.POST.get("quantity"))
    messages.success(request, "Cart updated.")
    return redirect("cart")


@require_http_methods(["POST"])
def cart_remove(request):
    CartService.remove(request.session, request.POST.get("product_id"))
    messages.success(request, "Item removed.")
    return redirect("cart")


@login_required
@require_http_methods(["GET", "POST"])
def checkout_view(request):
    """
    Checkout = payment gateway selection ONLY.
    Address is selected in cart and stored in session.
    """
    cart_items, cart_subtotal, cart_total = CartService.items_and_totals(request.session)
    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("product_list")

    subject = get_subject_member(request)

    address_id = CartService.get_selected_address_id(request.session)
    if not address_id:
        messages.info(request, "Select delivery address in cart first.")
        return redirect("cart")

    address = Coordinate.objects.filter(user=subject, id=address_id).first()
    if not address:
        messages.info(request, "Selected address invalid. Select again.")
        return redirect("cart")

    # for now only Razorpay, later load from tenant settings table
    payment_gateways = [
        {"key": "razorpay", "label": "Razorpay", "desc": "UPI, Cards, NetBanking"},
    ]

    if request.method == "POST":
        gateway = (request.POST.get("gateway") or "razorpay").strip().lower()
        allowed = {g["key"] for g in payment_gateways}
        if gateway not in allowed:
            messages.error(request, "Gateway not available.")
            return redirect("checkout")

        order = OrderService.create_order_from_cart(
            tenant=request.tenant,
            subject=subject,
            cart_items=cart_items,
            address_id=address.id,
        )
        CartService.clear(request.session)

        # you already redirect to payment_page in your project
        return redirect("payment_page", order_id=order.id)

    return render(request, _theme_path(request, "checkout.html"), {
        "cart_items": cart_items,
        "cart_total": cart_total,
        "selected_address": address,
        "payment_gateways": payment_gateways,
        "selected_gateway": "razorpay",
    })

@login_required
def payment_page(request, order_id):
    subject = get_subject_member(request)

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        subject=subject,
    )

    return render(request, _theme_path(request, "payment_page.html"), {
        "order": order,
    })

@login_required
def my_orders(request):
    subject = get_subject_member(request)
    orders = OrderService.get_customer_orders(subject=subject)  # exists in your OrderService :contentReference[oaicite:9]{index=9}
    return render(request, _theme_path(request, "previous_order_listing.html"), {"orders": orders})
    
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

    template = get_template("orders/storefront/invoice.html")  # fixed path
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
