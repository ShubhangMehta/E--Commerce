from django.urls import path
from catalog.views.single_template import (
    single_product_list_view,
    single_product_detail_view
)
from catalog.views import pages as dashboard_views

app_name = "catalog"

urlpatterns = [
    path("products/", single_product_list_view, name="single-product-list"),
    path("products/<int:product_id>/", single_product_detail_view, name="single-product-detail"),
    path("product/", dashboard_views.product_list, name="product_list"),
    path("product/create/", dashboard_views.product_create, name="product_create"),
    path("product/<int:pk>/edit/", dashboard_views.product_edit, name="product_edit"),
    path("product/<int:pk>/delete/", dashboard_views.product_delete, name="product_delete"),
    
]


