from django.shortcuts import render, get_object_or_404
from catalog.services.single_service import SingleProductService
from catalog.models import SingleProduct


def single_product_list_view(request):
    service = SingleProductService()
    products = service.get_available_products()

    return render(
        request,
        "catalog/single_product_list.html",
        {"products": products},
    )


def single_product_detail_view(request, product_id):
    product = get_object_or_404(
        SingleProduct.objects.prefetch_related("images"),
        id=product_id,
        availability=True,
    )

    return render(
        request,
        "catalog/single_product_detail.html",
        {"product": product},
    )
