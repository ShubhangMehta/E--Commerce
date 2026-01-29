from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import SingleProduct
from catalog.forms import SingleProductForm


# LIST PRODUCTS
def product_list(request):
    products = SingleProduct.objects.all()

    return render(
        request,
        "catalog/dashboard/product_list.html",
        {
            "products": products
        }
    )


# CREATE PRODUCT
def product_create(request):
    if request.method == "POST":
        form = SingleProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("catalog:product_list")
    else:
        form = SingleProductForm()

    return render(
        request,
        "catalog/dashboard/product_form.html",
        {
            "form": form,
            "title": "Create Product"
        }
    )


# EDIT PRODUCT
def product_edit(request, pk):
    product = get_object_or_404(SingleProduct, pk=pk)

    if request.method == "POST":
        form = SingleProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("catalog:product_list")
    else:
        form = SingleProductForm(instance=product)

    return render(
        request,
        "catalog/dashboard/product_form.html",
        {
            "form": form,
            "title": "Edit Product"
        }
    )


# DELETE PRODUCT
def product_delete(request, pk):
    product = get_object_or_404(SingleProduct, pk=pk)

    if request.method == "POST":
        product.delete()
        return redirect("catalog:product_list")

    return render(
        request,
        "catalog/dashboard/product_confirm_delete.html",
        {
            "product": product
        }
    )
