from django.urls import path
from . import views

urlpatterns=[
    path('', views.home, name='home'),
    path("billing/success/", views.billing_success, name="billing_success"),
    path("billing/cancel/", views.billing_cancel, name="billing_cancel"),
    path('create-tenant/', views.create_tenant,name='create_tenant'),
    path('raise-ticket/', views.raise_ticket, name='raise_ticket'),
    path("refund/<int:order_id>/", views.request_refund, name="request_refund"),
    path("admin/refund/<int:order_id>/approve/", views.approve_refund, name="approve_refund"),
    path("admin/refund/<int:order_id>/reject/", views.reject_refund, name="reject_refund"),
]