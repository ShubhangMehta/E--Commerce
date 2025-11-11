from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("pricing/", views.pricing_page, name="pricing"),              # ✅ add this
    path("checkout/start/", views.start_subscription, name="start"),   # existing ok
    path("webhook/razorpay/", views.razorpay_webhook, name="webhook"),
    path("checkout/", views.checkout_view, name="checkout"),           # optional legacy page
]
