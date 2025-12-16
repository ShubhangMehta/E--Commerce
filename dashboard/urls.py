from django.urls import path
from . import views
from customers import views as customers_views

urlpatterns = [
    #path("themes/", views.theme_settings, name="theme_settings"),

    #Razorpay Payment Urls; Just used simple names here easy to comprehend and change later if needed
    path("billing/renew/", customers_views.billing_renew, name="billing_renew"),
    path("billing/success/", customers_views.billing_success, name="billing_success"),
    path("billing/cancel/", customers_views.billing_cancel, name="billing_cancel"),
    path("billing/plans/", customers_views.billing_plans, name="billing_plans"),

    #Razorpay webhook endpoint
    #path("razorpay/webhook/", rzp_webhook_views.razorpay_webhook, name="razorpay_webhook"),

]