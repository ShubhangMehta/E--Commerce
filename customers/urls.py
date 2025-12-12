from django.urls import path
from . import views, rzp_webhook_views
from django.contrib import admin

urlpatterns=[
    path('create-tenant/', views.create_tenant,name='create_tenants'),
    path("admin/", admin.site.urls),
    path('',views.home,name='home'),
    path('raise-ticket/', views.raise_ticket, name='raise_ticket'),
    path('razorpay/webhook/', rzp_webhook_views.razorpay_webhook, name='razorpay_webhook'),
    #path("test-billing/", views.test_billing, name="test_billing"),
]

# urlpatterns = [
#     path('plans/', views.plans, name='plans'),
#     path('subscription/', views.RzpSubscription, name='subscription'),
#     path('renew/<int:subscription_id>/', views.start_subscription, name='renew'),
#     #path('update-plan/<int:subscription_id>/', views.update_plan, name='update_plan'),
#     #path('mark-paid/<int:invoice_id>/', views.mark_invoice_paid, name='mark_invoice_paid'),
#     path('create-tenant/', views.create_tenant,name='create_tenants'),
#     path('refund-request/', views.refund_request, name='refund_request'),

#     # Razorpay billing from customers app
#     path("subscription/start/", views.start_subscription, name="rzp_start"),
#     #path("billing/checkout/", views.checkout_view, name="rzp_checkout"),
#     path("webhook/razorpay/", views.razorpay_webhook, name="razorpay_webhook"),
# ]