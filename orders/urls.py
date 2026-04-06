from django.urls import path
from .views import pages as dashboard_views
from .views import storefront as storefront_views
from orders.api.views import StartPaymentAPIView

urlpatterns = [
    # TENANT DASHBOARD ORDERS ONLY
    path("orders/", dashboard_views.OrderListView.as_view(), name="dashboard_order_list"),
    path("orders/<int:pk>/", dashboard_views.OrderDetailView.as_view(), name="dashboard_order_detail"),
    #path("orders/<int:order_id>/invoice/", dashboard_views.invoice_view, name="invoice"),
    #path("orders/<int:order_id>/invoice/pdf/", dashboard_views.invoice_pdf, name="invoice_pdf"),

    # TENANT DASHBOARD ORDERS ONLY
    path("orders/", dashboard_views.OrderListView.as_view(), name="dashboard_order_list"),
    path("orders/<int:pk>/", dashboard_views.OrderDetailView.as_view(), name="dashboard_order_detail"),

    #API ENDPOINTS FOR STARTING PAYMENT
    path("orders/<int:order_id>/start-payment/", StartPaymentAPIView.as_view(), name="api_start-payment"),
]
