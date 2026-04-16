from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from django.db import transaction
from orders.models import Coupon
from catalog.models import SingleProduct
from users.models import SubjectMember
from decimal import Decimal

# If you already have an Order model in your project, import it here.
# Example:
# from orders.models import Order, OrderItem

def _theme_path(request, template_name: str) -> str:

    theme = getattr(request.tenant, "theme", "default") or "default"
    return f"themes/{theme}/{template_name}"

def index(request):
    featured_products = (
        SingleProduct.objects
        .filter(is_featured=True)
        .prefetch_related("images")
        .order_by("featured_order")[:3]
    )

    # Attach banner & product images safely
    for product in featured_products:
        product.banner_image = next(
            (img for img in product.images.all() if img.image_type == "banner"),
            None
        )
        product.product_image = next(
            (img for img in product.images.all() if img.image_type == "product"),
            None
        )
#   # ✅ Role Check
#   is_owner = False
#   if request.user.is_authenticated:
#       member = SubjectMember.objects.filter(
#           global_user_id=request.user.id
#       ).first()
#
#       if member and member.role == "OWNER":
#           is_owner = True

    context = {
        "featured_products": featured_products,
        "product_count": getattr(request.tenant, "product_count", None),
        "order_count": getattr(request.tenant, "order_count", None),
        "visitor_count": getattr(request.tenant, "visitor_count_7d", None),
        #is_owner": is_owner,
    }

    return render(request, _theme_path(request, "index.html"), context)

# -----------------------------
# CART (Session-based reference implementation)
# -----------------------------

# def _get_cart(session) -> dict:
#     """
#     Cart stored in session as:
#       cart = { "<product_id>": {"qty": int} }
#     """
#     return session.get("cart", {})


# def _set_cart(session, cart: dict) -> None:
#     session["cart"] = cart
#     session.modified = True


# def _cart_items_and_totals(cart: dict):
#     """
#     Returns (items, subtotal, total). Shipping/tax can be added later.
#     Each item: {product, quantity, line_total}
#     """
#     product_ids = [int(pid) for pid in cart.keys()] if cart else []
#     products = {p.id: p for p in SingleProduct.objects.filter(id__in=product_ids)}

#     items = []
#     subtotal = 0

#     for pid_str, data in cart.items():
#         pid = int(pid_str)
#         product = products.get(pid)
#         if not product:
#             continue
#         qty = int(data.get("qty", 1))
#         line_total = (product.price or 0) * qty
#         subtotal += line_total
#         items.append(
#             {
#                 "product": product,
#                 "quantity": qty,
#                 "line_total": line_total,
#             }
#         )

#     total = subtotal
#     return items, subtotal, total


# @require_http_methods(["GET", "POST"])
# def cart(request):
#     """
#     Shows cart. Optional: POST can add items if you want.
#     Template: cart.html expects cart_items, cart_total, cart_subtotal (optional).
#     """
#     # Optional add-to-cart via POST from product_list template
#     if request.method == "POST":
#         product_id = request.POST.get("product_id")
#         if product_id:
#             cart_data = _get_cart(request.session)
#             cart_data.setdefault(str(product_id), {"qty": 0})
#             cart_data[str(product_id)]["qty"] = int(cart_data[str(product_id)]["qty"]) + 1
#             _set_cart(request.session, cart_data)
#             messages.success(request, "Added to cart.")
#             return redirect("cart")

    cart_data = _get_cart(request.session)
    cart_items, cart_subtotal, cart_total = _cart_items_and_totals(cart_data)

    #  COUPON LOGIC STARTS HERE
    discount = 0
    coupon = None

    coupon_id = request.session.get("coupon_id")

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)

            if coupon.is_valid(cart_subtotal):

                

                discount = (cart_subtotal * coupon.discount_percent) / Decimal("100")

                # apply max discount limit
                if coupon.max_discount:
                    discount = min(discount, coupon.max_discount)

            else:
                # remove invalid coupon
                request.session.pop("coupon_id", None)

        except Coupon.DoesNotExist:
            request.session.pop("coupon_id", None)

    # final total after discount
    final_total = cart_subtotal - discount

    context = {
        "cart_items": cart_items,
        "cart_subtotal": cart_subtotal,
        "cart_total": final_total,   
        "discount": discount,
        "applied_coupon": coupon,
        "shipping_total": 0,
        "tax_total": 0,
    }
    return render(request, _theme_path(request, "cart.html"), context)


# @require_http_methods(["POST"])
# def cart_update(request):
#     """
#     Updates quantity for a product in cart.
#     Template uses URL name: cart_update
#     """
#     product_id = request.POST.get("product_id")
#     qty = request.POST.get("quantity")


    if not product_id or not qty:
        messages.error(request, "Invalid cart update.")
        return redirect("themes:cart")

#     if not product_id or not qty:
#         messages.error(request, "Invalid cart update.")
#         return redirect("cart")


#     try:
#         qty_int = max(1, int(qty))
#     except ValueError:
#         messages.error(request, "Quantity must be a number.")
#         return redirect("cart")

#     cart_data = _get_cart(request.session)
#     if str(product_id) in cart_data:
#         cart_data[str(product_id)]["qty"] = qty_int
#         _set_cart(request.session, cart_data)
#         messages.success(request, "Cart updated.")
#     return redirect("cart")


# @require_http_methods(["POST"])
# def cart_remove(request):
#     """
#     Removes a product from cart.
#     Template uses URL name: cart_remove
#     """
#     product_id = request.POST.get("product_id")
#     if not product_id:
#         return redirect("cart")

#     cart_data = _get_cart(request.session)
#     cart_data.pop(str(product_id), None)
#     _set_cart(request.session, cart_data)
#     messages.success(request, "Item removed.")
#     return redirect("cart")

# -----------------------------
# AUTH PAGES
# -----------------------------

@require_http_methods(["GET", "POST"])
def signup(request):
    """
    Signup page.
    Template: signup.html expects 'form'
    """
    if request.user.is_authenticated:
        return redirect("users:profile")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created.")
            return redirect("users:profile")
        messages.error(request, "Please correct the errors below.")

    return render(request, _theme_path(request, "signup.html"), {"form": form})


# If you already use Django's LoginView / LogoutView, keep using that.
# The templates you generated will work with LoginView (login.html) by default.

# -----------------------------
# PROFILE
# -----------------------------

@login_required
def profile(request):
    """
    Profile page.
    Template: profile.html expects user and optionally recent_orders.
    """
    # If you have a real Order model, query recent orders here and pass as recent_orders.
    recent_orders = request.session.get("orders_history", [])[:5]

    return render(
        request,
        _theme_path(request, "profile.html"),
        {"recent_orders": recent_orders},
    )

def previous_order_listing(request):
    theme = request.tenant.theme
    return render(request,f"themes/{theme}/previous_order_listing.html")
