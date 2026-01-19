from django.shortcuts import render, get_object_or_404
from catalog.models import SingleProduct


def index(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/index.html")


def product_list(request):
    theme = request.tenant.theme
    products = SingleProduct.objects.all()
    return render(
        request,
        f"themes/{theme}/product_list.html",
        {"products": products},
    )


def product_detail(request, id):
    theme = request.tenant.theme
    product = get_object_or_404(SingleProduct, id=id)
    return render(
        request,
        f"themes/{theme}/product_detail.html",
        {"product": product},
    )


def cart(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/cart.html")


def checkout(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/checkout.html")


def profile(request):
    theme = request.tenant.theme
    return render(request, f"themes/{theme}/profile.html")

