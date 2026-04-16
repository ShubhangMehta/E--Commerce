from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.http import require_http_methods
from django.db import connection
from catalog.models import SingleProduct

# If you already have an Order model in your project, import it here.
# Example:
# from orders.models import Order, OrderItem

def _theme_path(request, template_name: str) -> str:
    tenant = getattr(request, "tenant", None) or getattr(connection, "tenant", None)
    theme = getattr(tenant, "theme", None) or "default"
    print(f"DEBUG: Rendering template for theme '{theme}' with template name '{template_name}'")
    print("schema:", getattr(tenant, "schema_name", None), "themes:", theme)
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
