from django.urls import path
from catalog.views.single_template import (
    single_product_list_view,
    single_product_detail_view,
    add_to_cart_view,
)

from catalog.views.multi_template import (
    multi_product_list_view,
    multi_product_detail_view,
)

urlpatterns = [
    path("products/", single_product_list_view, name="single-product-list"),
    path("products/<int:product_id>/", single_product_detail_view, name="single-product-detail"),
    path("cart/add/<int:product_id>/", add_to_cart_view, name="add-to-cart"),
    path("multiproducts/", multi_product_list_view, name="multi-product-list"),
    path("multiproducts/<int:product_id>/", multi_product_detail_view, name="multi-product-detail"),

]
