from django.shortcuts import render, get_object_or_404
from catalog.services.single_service import SingleProductService
from catalog.models import SingleProduct


def single_product_list_view(request):
    products = SingleProduct.objects.prefetch_related("images")

    theme = request.tenant.theme or "default"
    theme_base = f"themes/{theme}/storefront.html"

    return render(
        request,
        "catalog/single_product_list.html",
        {
            "products": products,
            "theme_base": theme_base,
        }
    )



def single_product_detail_view(request, id):
    product = get_object_or_404(
        SingleProduct.objects.prefetch_related("images"),
        id=id
    )

    theme = request.tenant.theme or "default"
    theme_base = f"themes/{theme}/storefront.html"

    primary_image = product.images.filter(is_primary=True).first() \
                    or product.images.first()

    return render( 
        request,
        "catalog/single_product_detail.html",
        {
            "product": product,
            "primary_image": primary_image,
            "theme_base": theme_base,
        }
    )
