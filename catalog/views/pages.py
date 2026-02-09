from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import SingleProduct
from catalog.forms import SingleProductForm, ProductImageFormSet



# LIST PRODUCTS
def product_list(request):
    products = SingleProduct.objects.prefetch_related("images")

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
        formset = ProductImageFormSet(
            request.POST,
            request.FILES
        )

        if form.is_valid() and formset.is_valid():
            product = form.save()

            images = formset.save(commit=False)
            for image in images:
                image.product = product
                image.save()

            return redirect("catalog:product_list")

    else:
        form = SingleProductForm()
        formset = ProductImageFormSet()

    return render(
        request,
        "catalog/dashboard/product_form.html",
        {
            "form": form,
            "formset": formset,
            "title": "Create Product"
        }
    )

# EDIT PRODUCT
def product_edit(request, pk):
    product = get_object_or_404(SingleProduct, pk=pk)

    if request.method == "POST":
        form = SingleProductForm(request.POST, instance=product)
        formset = ProductImageFormSet(
            request.POST,
            request.FILES,
            instance=product
        )

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("catalog:product_list")

    else:
        form = SingleProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)

    return render(
        request,
        "catalog/dashboard/product_form.html",
        {
            "form": form,
            "formset": formset,
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
