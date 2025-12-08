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
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/index.html")

def product_list(request):
    theme = request.tenant.theme
    products = Product.objects.all()
    return render(request, f"themes/{theme}/product_list.html", {"products": products})

def product_detail(request, id):
    theme = request.tenant.theme
    product = get_object_or_404(Product, id=id)
    return render(request, f"themes/{theme}/product_detail.html", {"product": product})

def cart(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/cart.html")

def checkout(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/checkout.html")

