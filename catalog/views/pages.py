from django.shortcuts import render, redirect, get_object_or_404
from catalog.models import SingleProduct, SingleProductImage
from catalog.forms import SingleProductForm, ProductImageFormSet, BannerForm, CategoryForm, SubCategoryForm


# LIST PRODUCTS
def product_list(request):
    products = SingleProduct.objects.select_related(
    "category",
    "sub_category"
    ).prefetch_related("images")
    return render(
        request,
        "catalog/dashboard/product_list.html",
        {
            "products": products
        }
    )

def product_create(request):

    # CATEGORY FORM
    if request.method == "POST" and "create_category" in request.POST:
        category_form = CategoryForm(request.POST)
        subcategory_form = SubCategoryForm()

        if category_form.is_valid():
            category_form.save()
            return redirect("catalog:product_create")

        form = SingleProductForm()
        formset = ProductImageFormSet()

    # SUBCATEGORY FORM
    elif request.method == "POST" and "create_subcategory" in request.POST:
        subcategory_form = SubCategoryForm(request.POST)
        category_form = CategoryForm()

        if subcategory_form.is_valid():
            subcategory_form.save()
            return redirect("catalog:product_create")

        form = SingleProductForm()
        formset = ProductImageFormSet()

    # PRODUCT FORM
    elif request.method == "POST":
        form = SingleProductForm(request.POST)
        category_form = CategoryForm()
        subcategory_form = SubCategoryForm()

        if form.is_valid():
            product = form.save(commit=False)

            if product.is_featured:
                featured_count = SingleProduct.objects.filter(is_featured=True).count()

                if featured_count >= 3:
                    form.add_error(None, "You can only feature 3 products.")
                    formset = ProductImageFormSet(request.POST, request.FILES)

                else:
                    product.save()

                    formset = ProductImageFormSet(
                        request.POST,
                        request.FILES,
                        instance=product
                    )

                    if formset.is_valid():
                        formset.save()
                        return redirect("catalog:product_list")

            else:
                product.save()

                formset = ProductImageFormSet(
                    request.POST,
                    request.FILES,
                    instance=product
                )

                if formset.is_valid():
                    formset.save()
                    return redirect("catalog:product_list")

        else:
            formset = ProductImageFormSet(request.POST, request.FILES)

    else:
        form = SingleProductForm()
        formset = ProductImageFormSet()
        category_form = CategoryForm()
        subcategory_form = SubCategoryForm()

    return render(
        request,
        "catalog/dashboard/product_form.html",
        {
            "form": form,
            "formset": formset,
            "category_form": category_form,
            "subcategory_form": subcategory_form,
            "title": "Create Product"
        }
    )

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
            product = form.save(commit=False)

            if product.is_featured:
                featured_count = SingleProduct.objects.filter(
                    is_featured=True
                ).exclude(id=product.id).count()

                if featured_count >= 3:
                    form.add_error(None, "You can only feature 3 products.")

                else:
                    product.save()
                    formset.save()
                    return redirect("catalog:product_list")

            else:
                product.save()
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
            "category_form": CategoryForm(),
            "subcategory_form": SubCategoryForm(),
            "title": "Edit Product"
        }
    )


def banner_list(request):
    banners = SingleProductImage.objects.filter(image_type="banner")

    form = BannerForm()

    if request.method == "POST":
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            banner = form.save(commit=False)
            banner.image_type = "banner"
            banner.save()
            return redirect("catalog:banner_list")

    return render(
        request,
        "catalog/dashboard/banner_list.html",
        {"banners": banners, "form": form}
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
