from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.conf import settings
from django.conf.urls.static import static


def admin_login_redirect(request):
    next_url = request.GET.get("next", "/index/")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/login/"
    return redirect("/login/?" + urlencode({"next": next_url}))


urlpatterns = [
    #Webhook for Tenant admin payments
    #path("razorpay/webhook/", rzp_webhook_views.razorpay_webhook, name="razorpay_webhook"),

    #Webhook from end user orders
    path("orders/razorpay/webhook/", rzp_webhook_views.TenantRazorpayWebhookAPIView.as_view(), name="orders_razorpay_webhook"),
    
    # Keep admin enabled
    path("admin/login/", admin_login_redirect, name="admin_login_redirect"),
    path("admin/", admin.site.urls),

    # Your app routes
    path("", include("customers.urls")),
    path("", include("accounts.urls")),
]
