from django.shortcuts import render, get_object_or_404
from catalog.services.single_service import SingleProductService
from catalog.models import SingleProduct
from django.shortcuts import redirect


def single_product_list_view(request):
    query = request.GET.get("q", "")
    service = SingleProductService()
    products = service.get_available_products(query=query)

    return render(
        request,
        "catalog/single_product_list.html",
        {
            "products": products,
            "query": query,
        },
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


def add_to_cart_view(request, product_id):
    cart = request.session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session["cart"] = cart
    return redirect("single-product-list")
