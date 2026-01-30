
# from django.urls import path
# from . import views

# urlpatterns = [
#     path("create/", views.order_create, name="order_create"),
#     path("", views.order_list, name="order_list"),
#     # path("<int:order_id>/", views.order_detail, name="order_detail"),
#     path("<int:pk>/", views.order_detail, name="order_detail"),
#     path("<int:order_id>/invoice/", views.invoice_view, name="invoice"),
#     # path("<int:order_id>/invoice/pdf/", views.invoice_pdf, name="invoice_pdf"),
#     path("orders/", views.order_list, name="order_list"),
    
#     path("invoice/<int:order_id>/", views.invoice_pdf, name="invoice_pdf"),
#     path("orders/", views.order_list, name="order_list"),
    
#     path("orders/<int:id>/", views.order_detail, name="order_detail")

# ]






from django.urls import path
from . import views

urlpatterns = [
    # Create order
    path("create/", views.order_create, name="order_create"),

    # Order list
    path("", views.order_list, name="order_list"),

    # Order detail
    path("<int:order_id>/", views.order_detail, name="order_detail"),

    # Invoice (HTML view)
    path("<int:order_id>/invoice/", views.invoice_view, name="invoice"),

    # Invoice PDF download
    path("<int:order_id>/invoice/pdf/", views.invoice_pdf, name="invoice_pdf"),
]
