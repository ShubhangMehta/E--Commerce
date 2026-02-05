from django.shortcuts import render, get_object_or_404
from catalog.services.multi_service import MultiProductService
from catalog.models import MultiProduct, MultiCategory

#from catalog.permissions import multi_product_only

#@multi_product_only
def multi_product_list_view(request):
    query = request.GET.get("q", "")
    category_id = request.GET.get("category")

    service = MultiProductService()
    products = service.get_products(
        query=query,
        category_id=category_id
    )

    categories = MultiCategory.objects.all()

    return render(
        request,
        "catalog/multi_temp/multi_product_list.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "selected_category": category_id,
        },
    )

#@multi_product_only
def multi_product_detail_view(request, product_id):
    product = get_object_or_404(
        MultiProduct.objects.prefetch_related("images", "variants__variant_value"),
        id=product_id,
        availability=True,
    )

    return render(
        request,
        "catalog/multi_temp/multi_product_detail.html",
        {"product": product},
    )
