from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from django.db import transaction

from catalog.models import SingleProduct

# If you already have an Order model in your project, import it here.
# Example:
# from orders.models import Order, OrderItem

def _theme_path(request, template_name: str) -> str:
    """
    Returns the theme-aware template path.
    Works for all themes as long as templates exist under: templates/themes/<theme>/
    """
    theme = getattr(request.tenant, "theme", "default") or "default"
    return f"themes/{theme}/{template_name}"


def index(request):
    """
    Home page.
    Optional: You can pass featured_products + counts pulled from tenant if you want.
    """
    # Example for featured list: you can change filter later (e.g. is_featured=True)
    featured_products = SingleProduct.objects.all()[:6]

    context = {
        "featured_products": featured_products,
        "product_count": getattr(request.tenant, "product_count", None),
        "order_count": getattr(request.tenant, "order_count", None),
        "visitor_count": getattr(request.tenant, "visitor_count_7d", None),
    }
    return render(request, _theme_path(request, "index.html"), context)


def product_list(request):
    """
    Product listing page with basic search/sort.
    Template: product_list.html expects 'products'.
    """
    qs = SingleProduct.objects.all()

    q = (request.GET.get("q") or "").strip()
    if q:
        # Adjust fields if your model uses different names
        qs = qs.filter(name__icontains=q) | qs.filter(description__icontains=q)

    sort = request.GET.get("sort") or ""
    if sort == "price_asc":
        qs = qs.order_by("price")
    elif sort == "price_desc":
        qs = qs.order_by("-price")
    elif sort == "new":
        # If you have created_at; otherwise fallback to id desc
        if hasattr(SingleProduct, "created_at"):
            qs = qs.order_by("-created_at")
        else:
            qs = qs.order_by("-id")

    return render(
        request,
        _theme_path(request, "product_list.html"),
        {"products": qs},
    )


def product_detail(request, id):
    """
    Product details page.
    Template: product_details.html expects 'product' (and optionally 'related_products').
    """
    product = get_object_or_404(SingleProduct, id=id)

    # Optional related products. Adjust logic as needed.
    related_products = SingleProduct.objects.exclude(id=product.id)[:4]

    return render(
        request,
        _theme_path(request, "product_details.html"),
        {"product": product, "related_products": related_products},
    )


# -----------------------------
# CART (Session-based reference implementation)
# -----------------------------

def _get_cart(session) -> dict:
    """
    Cart stored in session as:
      cart = { "<product_id>": {"qty": int} }
    """
    return session.get("cart", {})


def _set_cart(session, cart: dict) -> None:
    session["cart"] = cart
    session.modified = True


def _cart_items_and_totals(cart: dict):
    """
    Returns (items, subtotal, total). Shipping/tax can be added later.
    Each item: {product, quantity, line_total}
    """
    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = {p.id: p for p in SingleProduct.objects.filter(id__in=product_ids)}

    items = []
    subtotal = 0

    for pid_str, data in cart.items():
        pid = int(pid_str)
        product = products.get(pid)
        if not product:
            continue
        qty = int(data.get("qty", 1))
        line_total = (product.price or 0) * qty
        subtotal += line_total
        items.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line_total,
            }
        )

    total = subtotal
    return items, subtotal, total


@require_http_methods(["GET", "POST"])
def cart(request):
    """
    Shows cart. Optional: POST can add items if you want.
    Template: cart.html expects cart_items, cart_total, cart_subtotal (optional).
    """
    # Optional add-to-cart via POST from product_list template
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        if product_id:
            cart_data = _get_cart(request.session)
            cart_data.setdefault(str(product_id), {"qty": 0})
            cart_data[str(product_id)]["qty"] = int(cart_data[str(product_id)]["qty"]) + 1
            _set_cart(request.session, cart_data)
            messages.success(request, "Added to cart.")
            return redirect("cart")

    cart_data = _get_cart(request.session)
    cart_items, cart_subtotal, cart_total = _cart_items_and_totals(cart_data)

    context = {
        "cart_items": cart_items,
        "cart_subtotal": cart_subtotal,
        "cart_total": cart_total,
        # placeholders
        "shipping_total": 0,
        "tax_total": 0,
    }
    return render(request, _theme_path(request, "cart.html"), context)


@require_http_methods(["POST"])
def cart_update(request):
    """
    Updates quantity for a product in cart.
    Template uses URL name: cart_update
    """
    product_id = request.POST.get("product_id")
    qty = request.POST.get("quantity")

    if not product_id or not qty:
        messages.error(request, "Invalid cart update.")
        return redirect("cart")

    try:
        qty_int = max(1, int(qty))
    except ValueError:
        messages.error(request, "Quantity must be a number.")
        return redirect("cart")

    cart_data = _get_cart(request.session)
    if str(product_id) in cart_data:
        cart_data[str(product_id)]["qty"] = qty_int
        _set_cart(request.session, cart_data)
        messages.success(request, "Cart updated.")
    return redirect("cart")


@require_http_methods(["POST"])
def cart_remove(request):
    """
    Removes a product from cart.
    Template uses URL name: cart_remove
    """
    product_id = request.POST.get("product_id")
    if not product_id:
        return redirect("cart")

    cart_data = _get_cart(request.session)
    cart_data.pop(str(product_id), None)
    _set_cart(request.session, cart_data)
    messages.success(request, "Item removed.")
    return redirect("cart")


# -----------------------------
# CHECKOUT + ORDERS (stubs you can connect to your real orders app)
# -----------------------------

@require_http_methods(["GET", "POST"])
@login_required
def checkout(request):
    """
    Checkout page.
    - Shows cart summary on GET
    - On POST, creates an order (stub) and redirects to success

    Templates:
      - checkout.html expects cart_items, cart_total and optionally 'form'
      - order_success.html expects 'order' (and optionally 'order_items')
    """
    cart_data = _get_cart(request.session)
    cart_items, cart_subtotal, cart_total = _cart_items_and_totals(cart_data)

    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("product_list")

    if request.method == "POST":
        # If you have a real Order model, create it here.
        # This stub stores a minimal order in session.
        with transaction.atomic():
            order_id = request.session.get("last_order_id", 0) + 1
            request.session["last_order_id"] = order_id

            order = {
                "id": order_id,
                "status": "Processing",
                "total": cart_total,
                "payment_status": "Pending",
            }

            # Keep simple history for "previous_order_listing"
            history = request.session.get("orders_history", [])
            history.insert(
                0,
                {
                    "id": order_id,
                    "status": order["status"],
                    "total": order["total"],
                    "created_at": None,  # optionally store timestamp as string
                },
            )
            request.session["orders_history"] = history
            request.session["last_order"] = order
            request.session.modified = True

            # Clear cart
            _set_cart(request.session, {})

        messages.success(request, "Order placed successfully.")
        return redirect("order_success")

    context = {
        "cart_items": cart_items,
        "cart_subtotal": cart_subtotal,
        "cart_total": cart_total,
        "shipping_total": 0,
        "tax_total": 0,
        # If you later use a real CheckoutForm, pass it as "form"
        "form": None,
    }
    return render(request, _theme_path(request, "checkout.html"), context)


@login_required
def previous_order_listing(request):
    """
    Lists previous orders.
    If you have a real Order model, replace session logic with DB queries.
    Template: previous_order_listing.html expects 'orders'
    """
    orders = request.session.get("orders_history", [])
    return render(
        request,
        _theme_path(request, "previous_order_listing.html"),
        {"orders": orders},
    )


@login_required
def order_success(request):
    """
    Order success page.
    Loads the last order from session (stub) or from DB if you have Order model.
    Template: order_success.html expects 'order' (and optionally 'order_items')
    """
    order = request.session.get("last_order")
    if not order:
        messages.info(request, "No recent order found.")
        return redirect("previous_order_listing")

    # If you have DB order items, load them here. For now, none.
    context = {
        "order": order,
        "order_items": None,
    }
    return render(request, _theme_path(request, "order_success.html"), context)


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
        return redirect("profile")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created.")
            return redirect("profile")
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





















# from django.shortcuts import render, get_object_or_404
# from catalog.models import SingleProduct


# def index(request):
#     theme = request.tenant.theme
#     return render(request, f"themes/{theme}/index.html")


# def product_list(request):
#     theme = request.tenant.theme
#     products = SingleProduct.objects.all()
#     return render(
#         request,
#         f"themes/{theme}/product_list.html",
#         {"products": products},
#     )


# def product_detail(request, id):
#     theme = request.tenant.theme
#     product = get_object_or_404(SingleProduct, id=id)
#     return render(
#         request,
#         f"themes/{theme}/product_detail.html",
#         {"product": product},
#     )


# def cart(request):
#     theme = request.tenant.theme
#     return render(request, f"themes/{theme}/cart.html")


# def checkout(request):
#     theme = request.tenant.theme
#     return render(request, f"themes/{theme}/checkout.html")


# def profile(request):
#     theme = request.tenant.theme
#     return render(request, f"themes/{theme}/profile.html")

