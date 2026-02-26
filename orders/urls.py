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
from .views import pages as dashboard_views
from .views import storefront as storefront_views
app_name='orders'
    

urlpatterns = [
    # TENANT DASHBOARD ORDERS ONLY
    path("orders/", dashboard_views.OrderListView.as_view(), name="dashboard_order_list"),
    path("orders/<int:pk>/", dashboard_views.OrderDetailView.as_view(), name="dashboard_order_detail"),
    #path("orders/<int:order_id>/invoice/", dashboard_views.invoice_view, name="invoice"),
    #path("orders/<int:order_id>/invoice/pdf/", dashboard_views.invoice_pdf, name="invoice_pdf"),

]