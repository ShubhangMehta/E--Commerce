from django.contrib import admin
from django.urls import path,include
from customers import rzp_webhook_views
#admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("customers.urls")),
    path("razorpay/webhook/", rzp_webhook_views.razorpay_webhook, name="razorpay_webhook"),
]
