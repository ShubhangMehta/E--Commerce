from django.shortcuts import render, get_object_or_404
from catalog.models import Product

# Create your views here.

def index(request):
    return render(request, f"themes/default/index.html")

def product_list(request):
    products = Product.objects.all()
    return render(request, f"themes/default/product_list.html", {"products": products})

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, f"themes/default/product_detail.html", {"product": product})

def cart(request):
    return render(request, f"themes/default/cart.html")

def checkout(request):
    return render(request, f"themes/default/checkout.html")

