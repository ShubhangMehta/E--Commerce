from django.urls import path
from . import views
from customers import views as customers_views

urlpatterns = [
    path("billing/renew/", customers_views.billing_renew, name="billing_renew"),
    path("billing/success/", customers_views.billing_success, name="billing_success"),
    path("billing/cancel/", customers_views.billing_cancel, name="billing_cancel"),
    path("billing/plans/", customers_views.billing_plans, name="billing_plans"),
]