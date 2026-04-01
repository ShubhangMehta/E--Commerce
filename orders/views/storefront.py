from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa

from orders.models import Order, Coupon
from users.models import Coordinate
from orders.services.cart_service import CartService
from orders.services.order_service import OrderService
from orders.services.pricing_service import PricingService
from users.views.theme_views import get_subject_member

# import theme helpers
from themes.views import _theme_path

def _get_coupon_from_session(session):
    """
    Reads Coupon code from session and returns Coupon instance or None.
    Assumes Coupon has unique code field.
    """
    code = CartService.get_coupon_code(session)
    if not code:
        return None
    try:
        return Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return None
    

@require_http_methods(["GET", "POST"])
def cart_view(request):
    """
    GET: render cart with address selection (right)
    POST:
        -   add productto cart 
        -   apply/remove coupon
        -   select address
    """
    subject = None
    if request.user.is_authenticated:
        subject = get_subject_member(request)
         
    # POST actions
    if request.method == "POST":
        # add product
        product_id = request.POST.get("product_id")
        if product_id:
            CartService.add(request.session, request.POST["product_id"], 1)
            messages.success(request, "Added to cart.")
            return redirect("cart")

        # apply/remove coupon
        if "coupon_code" in request.POST:
            CartService.set_coupon(request.session, request.POST.get("coupon_code"))
            messages.success(request, "Coupon updated.")
            return redirect("cart")

        # select address
        address_id = request.POST.get("address_id")
        if address_id:
            if not request.user.is_authenticated:
                messages.info(request, "Please login to select address.")
                return redirect("login")
            
            if not subject:
                messages.error(request, "Customer or Profile not found.")
                return redirect("cart")
            
            if not Coordinate.objects.filter(user=subject, id=address_id).exists():
                messages.error(request, "Address not found.")
                return redirect("cart")
            
            CartService.set_selected_address(request.session, int(address_id))
            messages.success(request, "Address selected.")
            return redirect("checkout")

    cart_items = CartService.build_items(request.session)
    Coupon = _get_coupon_from_session(request.session)
    pricing = PricingService.calculate_from_items(items=cart_items, coupon=Coupon)

    addresses = []
    if subject:
        addresses = Coordinate.objects.filter(user=subject).order_by("-is_default", "-id")

    context = {
        "cart_items": cart_items,
        
        # right panel
        "addresses": addresses,
        "selected_address_id": CartService.get_selected_address_id(request.session),

        # coupon
        "coupon_code": CartService.get_coupon_code(request.session),
        "applied_coupon": pricing["coupon"],

        # calculations
        "cart_subtotal": pricing["subtotal"],
        "shipping_total": pricing["shipping_amount"],
        "tax_total": pricing["tax_amount"],
        "discount_total": pricing["discount_amount"],
        "grand_total": pricing["total_amount"],

        "customer_name": subject.full_name if subject else "",
        "customer_email": subject.email if subject else "",
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
    Checkout = payment gateway selection only.
    Address is selected in cart and stored in session.
    """
    cart_items = CartService.build_items(request.session)
    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart")

    subject = get_subject_member(request)
    if not subject:
        messages.error(request, "Customer profile not found.")
        return redirect("cart")

    address_id = CartService.get_selected_address_id(request.session)
    if not address_id:
        messages.info(request, "Select delivery address in cart first.")
        return redirect("cart")

    address = Coordinate.objects.filter(user=subject, id=address_id).first()
    if not address:
        messages.info(request, "Selected address is invalid. Please select again.")
        return redirect("cart")

    coupon = _get_coupon_from_session(request.session)
    pricing = PricingService.calculate_from_items(items=cart_items, coupon=coupon)

    payment_gateways = [
        {
            "key": "razorpay",
            "label": "Razorpay",
            "desc": "UPI, Cards, NetBanking",
        },
    ]

    if request.method == "POST":
        gateway = (request.POST.get("gateway") or "razorpay").strip().lower()
        allowed_gateways = {g["key"] for g in payment_gateways}

        if gateway not in allowed_gateways:
            messages.error(request, "Gateway not available.")
            return redirect("checkout")

        order = OrderService.create_order_from_cart(
            tenant=request.tenant,
            subject=subject,
            cart_items=cart_items,
            address_id=address.id,
            coupon=coupon,
        )

        CartService.clear(request.session)
        messages.success(request, "Order created successfully.")
        return redirect("payment_page", order_id=order.id)

    return render(
        request,
        _theme_path(request, "checkout.html"),
        {
            "cart_items": cart_items,
            "selected_address": address,
            "payment_gateways": payment_gateways,
            "selected_gateway": "razorpay",

            "coupon_code": CartService.get_coupon_code(request.session),
            "applied_coupon": pricing["coupon"],

            "cart_subtotal": pricing["subtotal"],
            "shipping_total": pricing["shipping_amount"],
            "tax_total": pricing["tax_amount"],
            "discount_total": pricing["discount_amount"],
            "grand_total": pricing["total_amount"],

            "customer_name": subject.full_name,
            "customer_email": subject.email,
        },
    )

@login_required
def payment_page(request, order_id):
    subject = get_subject_member(request)

    order = get_object_or_404(
        Order.objects
        .filter(id=order_id, subject=subject)
        .select_related("subject")  #, "coordinate", "coupon"
        .prefetch_related("items__product"),
    )

    return render(request, _theme_path(request, "payment_page.html"), {
        "order": order,
        "order_items": order.items.all(),
    },
    )

@login_required
def my_orders(request):
    subject = get_subject_member(request)
    orders = OrderService.get_customer_orders(subject=subject)

    return render(
        request,
        _theme_path(request, "previous_order_listing.html"),
        {"orders": orders},
    )    

@login_required
@require_http_methods(["POST"])
def apply_coupon(request):
    code = (request.POST.get("coupon_code") or  "").strip()

    if not code:
        CartService.set_coupon(request.session, "")
        messages.info(request, "Coupon removed.")
        return redirect("cart")

    cart_items = CartService.build_items(request.session)
    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart")
    
    subtotal = PricingService.subtotal_from_items(cart_items)

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        CartService.set_coupon(request.session, "")
        messages.error(request, "Invalid coupon code.")
        return redirect("cart")

    if coupon.is_valid(subtotal):
        CartService.set_coupon(request.session, coupon.code)
        messages.success(request, "Coupon applied successfully!")
    else:
        CartService.set_coupon(request.session, "")
        messages.error(request, "Coupon not valid for this order.")

    return redirect("cart")

@login_required
def order_success_view(request, order_id):
    subject = get_subject_member(request)

    order = get_object_or_404(
        Order.objects
        .filter(subject=subject, id=order_id)
        .select_related("subject", "coordinate", "coupon")
        .prefetch_related("items__product"),
    )

    if order.payment_status != "paid":
        return redirect("payment_page", order_id=order.id)

    latest_payment = None
    if hasattr(order, "payments"):
        latest_payment = order.payments.order_by("-created_at").first()

    return render(
        request,
        _theme_path(request, "order_success.html"),
        {
            "order": order,
            "order_items": order.items.all(),
            "latest_payment": latest_payment,
        },
    )

@login_required
def order_detail_view(request, order_id):
    subject = get_subject_member(request)
    order = OrderService.get_customer_order_detail(subject=subject, order_id=order_id)

    return render(
        request,
        _theme_path(request, "cust_order_detail.html"),
        {
            "order": order,
            "items": order.items.all(),
        },
    )

@login_required
def invoice_view(request, order_id):
    subject = get_subject_member(request)
    order = OrderService.get_customer_order_detail(subject=subject, order_id=order_id)

    return render(
        request,
        _theme_path(request, "cust_invoice.html"),
        {
            "order": order,
            "items": order.items.all(),
        },
    )

@login_required
def invoice_pdf_view(request, order_id):
    subject = get_subject_member(request)
    order = OrderService.get_customer_order_detail(subject=subject, order_id=order_id)

    template = get_template(_theme_path(request, "cust_invoice.html"))
    html = template.render(
        {
            "order": order,
            "items": order.items.all(),
            "request": request,
        }
    )

    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    if pdf.err:
        return HttpResponse("Error generating PDF", status=500)

    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{order.id}.pdf"'
    return response

