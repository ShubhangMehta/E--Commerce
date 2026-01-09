from django.urls import path
from tenant_app.orders.views.order_list import OrderListView
from tenant_app.orders.views.order_create import OrderCreateView
from tenant_app.orders.views.order_detail import OrderDetailView

urlpatterns = [
    path("", OrderListView().get, name="order-list"),
    path("create/", OrderCreateView().get, name="order-create"),
    path("<int:pk>/", OrderDetailView().get, name="order-detail"),
]
