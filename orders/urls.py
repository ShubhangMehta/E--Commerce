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
    path("", views.order_list, name="order_list"),
    path("create/", views.order_create, name="order_create"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/invoice/", views.invoice_view, name="invoice"),
    # path("<int:order_id>/invoice/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    path("invoice/<int:order_id>/", views.invoice_pdf, name="invoice_pdf"),
    path("orders/", views.order_list, name="order_list"),
    # TENANT DASHBOARD ORDERS ONLY
    path("orders/", dashboard_views.OrderListView.as_view(), name="dashboard_order_list"),
    path("orders/<int:pk>/", dashboard_views.OrderDetailView.as_view(), name="dashboard_order_detail"),
    #path("orders/<int:order_id>/invoice/", dashboard_views.invoice_view, name="invoice"),
    #path("orders/<int:order_id>/invoice/pdf/", dashboard_views.invoice_pdf, name="invoice_pdf"),

]