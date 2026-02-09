from django.urls import path
from orders.views import storefront as views

app_name = "orders_storefront"  # namespace for reverse URL lookups

urlpatterns = [
    path("checkout/", views.checkout_view, name="checkout"),
    path("order-success/<int:order_id>/", views.order_success_view, name="order_success"),
    path("my-orders/", views.my_orders_view, name="my_orders"),
    path("order/<int:order_id>/", views.order_detail_view, name="order_detail"),
    path("invoice/<int:order_id>/", views.invoice_view, name="invoice"),
    path("invoice/<int:order_id>/pdf/", views.invoice_pdf_view, name="invoice_pdf"),
]
