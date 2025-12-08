from django.urls import path
from . import views

urlpatterns = [
    #path('billing/', views.home, name='billing_home'),
    path('plans/', views.plans, name='plans'),
<<<<<<< HEAD
    path('billing-cycle/', views.billing_cycle, name='billing_cycle'),
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path('payment-success/<int:invoice_id>/', views.payment_success, name='payment_success'),
    path('subscription/', views.subscription, name='subscription'),
    path('renew/<int:subscription_id>/', views.renew_subscription, name='renew'),
    path('update-plan/<int:subscription_id>/', views.update_plan, name='update_plan'),
    path('mark-paid/<int:invoice_id>/', views.mark_invoice_paid, name='mark_invoice_paid'),
<<<<<<< HEAD

    # Razorpay billing from customers app
    path("billing/pricing/", customer_views.pricing_page, name="rzp_pricing"),
    path("billing/checkout/start/", customer_views.start_subscription, name="rzp_start"),
    path("billing/checkout/", customer_views.checkout_view, name="rzp_checkout"),
    path("billing/webhook/razorpay/", customer_views.razorpay_webhook, name="rzp_webhook"),
=======
>>>>>>> 0078471 (mylatestcode)
=======
    #path('billing-cycle/', views.billing_cycle, name='billing_cycle'),
    #path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    #path('payment-success/<int:invoice_id>/', views.payment_success, name='payment_success'),
    path('subscription/', views.RzpSubscription, name='subscription'),
    path('renew/<int:subscription_id>/', views.start_subscription, name='renew'),
    #path('update-plan/<int:subscription_id>/', views.update_plan, name='update_plan'),
    #path('mark-paid/<int:invoice_id>/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('create-tenant/', views.create_tenant,name='create_tenants'),

    # Razorpay billing from customers app
    #path("pricing/", views.pricing_page, name="rzp_pricing"),
    path("subscription/start/", views.start_subscription, name="rzp_start"),
    #path("billing/checkout/", views.checkout_view, name="rzp_checkout"),
    path("webhook/razorpay/", views.razorpay_webhook, name="razorpay_webhook"),
>>>>>>> 69fec36 (Razorpay Integration)
]
