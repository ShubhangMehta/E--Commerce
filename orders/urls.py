# from django.urls import path
# from tenant_app.orders.views.order_list import OrderListView
# from tenant_app.orders.views.order_create import OrderCreateView
# from tenant_app.orders.views.order_detail import OrderDetailView

# urlpatterns = [
#     path("", OrderListView().get, name="order-list"),
#     path("create/", OrderCreateView().get, name="order-create"),
#     path("<int:pk>/", OrderDetailView().get, name="order-detail"),
# ]

from django.urls import path
from orders.views import pages as dashboard_views
from orders.views import storefront as storefront_views
from orders.api import views as PaymentAPI

urlpatterns = [    # TENANT DASHBOARD ORDERS ONLY
    path("orders/", dashboard_views.OrderListView.as_view(), name="dashboard_order_list"),
    path("orders/<int:pk>/", dashboard_views.OrderDetailView.as_view(), name="dashboard_order_detail"),

    # STOREFRONT ORDERS
    path("checkout/", storefront_views.checkout_view, name="checkout"),
    path("order-success/<int:order_id>/", storefront_views.order_success_view, name="order_success"),
    path("my-orders/", storefront_views.my_orders_view, name="my_orders"),
    path("order/<int:order_id>/", storefront_views.order_detail_view, name="order_detail"),
    path("invoice/<int:order_id>/", storefront_views.invoice_view, name="invoice"),
    path("invoice/<int:order_id>/pdf/", storefront_views.invoice_pdf_view, name="invoice_pdf"),

    #API ENDPOINTS FOR STARTING PAYMENT
    path("orders/<int:order_id>/start-payment/", PaymentAPI.StartPaymentAPIView.as_view(), name="api_start_payment"),
]
