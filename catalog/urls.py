from django.urls import path
from catalog.views.single_template import (
    single_product_list_view,
    single_product_detail_view,
)

urlpatterns = [
    path("products/", single_product_list_view, name="single-product-list"),
    path("products/<int:product_id>/", single_product_detail_view, name="single-product-detail"),
]