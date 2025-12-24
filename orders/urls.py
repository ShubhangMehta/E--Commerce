from django.urls import path
from .views.order_create import order_create
from .views.order_list import order_list
from .views.order_detail import order_detail

urlpatterns = [
    path("create/", order_create, name="order-create"),
    path("list/", order_list, name="order-list"),
    path("<int:order_id>/", order_detail, name="order-detail"),
]
