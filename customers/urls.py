from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='billing_home'),
    path('plans/', views.plans, name='plans'),
    path('billing-cycle/', views.billing_cycle, name='billing_cycle'),
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path('payment-success/<int:invoice_id>/', views.payment_success, name='payment_success'),
    path('subscription/', views.subscription, name='subscription'),
    path('renew/<int:subscription_id>/', views.renew_subscription, name='renew'),
    path('update-plan/<int:subscription_id>/', views.update_plan, name='update_plan'),
    path('mark-paid/<int:invoice_id>/', views.mark_invoice_paid, name='mark_invoice_paid'),
]
