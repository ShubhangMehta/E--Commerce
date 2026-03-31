from django.urls import path
from orders.views import pages as dashboard_views
from orders.views import storefront as storefront_views
from orders.api import views as PaymentAPI

urlpatterns = [    
    # TENANT DASHBOARD ORDERS ONLY
    path("orders/", dashboard_views.OrderListView.as_view(), name="dashboard_order_list"),
    path("orders/<int:pk>/", dashboard_views.OrderDetailView.as_view(), name="dashboard_order_detail"),

    # STOREFRONT ORDERS
    path("cart/", storefront_views.cart_view, name="cart"),
    path("cart/update/", storefront_views.cart_update, name="cart_update"),
    path("cart/remove/", storefront_views.cart_remove, name="cart_remove"),
    path("checkout/", storefront_views.checkout_view, name="checkout"),
    path("order-success/<int:order_id>/", storefront_views.order_success_view, name="order_success"),
    path("orders/<int:order_id>/status/", PaymentAPI.OrderStatusAPIView.as_view(), name="order_status_api"),
    path("order/<int:order_id>/", storefront_views.order_detail_view, name="order_detail"),
    path("invoice/<int:order_id>/", storefront_views.invoice_view, name="invoice"),
    path("invoice/<int:order_id>/pdf/", storefront_views.invoice_pdf_view, name="invoice_pdf"),

    #API ENDPOINTS FOR STARTING PAYMENT
    path("payment_page/<int:order_id>/", storefront_views.payment_page, name="payment_page"),
    path("orders/<int:order_id>/start-payment/", PaymentAPI.StartPaymentAPIView.as_view(), name="api_start_payment"),
]
