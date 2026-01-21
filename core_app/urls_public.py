from django.contrib import admin
<<<<<<< HEAD:core_app/urls_public.py
from django.urls import path,include
from customers import rzp_webhook_views
from django.conf import settings
from django.http import HttpResponse

urlpatterns = [
    path("razorpay/webhook/", rzp_webhook_views.razorpay_webhook, name="razorpay_webhook"),

    path(
        "billing/success/",
        lambda r: HttpResponse("Payment successful. Provisioning your site…"),
        name="billing_success",
    ),

    path(
        "billing/cancel/",
        lambda r: HttpResponse("Payment cancelled."),
        name="billing_cancel",
    ),

    path("admin/", admin.site.urls),

    path("", include("customers.urls")),

    # ✅ FIXED LINE
    path("backups/", include("backups.urls")),
]