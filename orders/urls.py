# ----from django.urls import path
#from .views.order_create import order_create
#from .views.order_list import order_list
#from .views.order_detail import order_detail

#urlpatterns = [
 #   path("create/", order_create, name="order-create"),
  #  path("list/", order_list, name="order-list"),
   # path("<int:order_id>/", order_detail, name="order-detail"),
#]
from django.urls import path
from . import views

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

]






