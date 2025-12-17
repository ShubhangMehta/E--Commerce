from django.urls import path
from . import views #, rzp_webhook_views
from django.contrib import admin

urlpatterns=[
    path('create-tenant/', views.create_tenant,name='create_tenants'),
    path("admin/", admin.site.urls),
    path('',views.home,name='home'),
    path('raise-ticket/', views.raise_ticket, name='raise_ticket'),
    #path('razorpay/webhook/', rzp_webhook_views.razorpay_webhook, name='razorpay_webhook'),
    #path("test-billing/", views.test_billing, name="test_billing"),
]
