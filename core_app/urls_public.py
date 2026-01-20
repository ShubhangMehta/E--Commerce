from django.urls import path, include
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from customers import rzp_webhook_views
from django.utils.http import url_has_allowed_host_and_scheme, urlencode

def admin_login_redirect(request):
    next_url = request.GET.get("next", "/admin/")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/login/"
    return redirect("/login/?" + urlencode({"next": next_url}))                                   

urlpatterns = [
    path("razorpay/webhook/", rzp_webhook_views.razorpay_webhook, name="razorpay_webhook"),
    path("billing/success/", lambda r: HttpResponse("Payment successful. Provisioning your site…"),
         name="billing_success"),
    path("billing/cancel/", lambda r: HttpResponse("Payment cancelled."), name="billing_cancel"),

    # Keep admin enabled
    path("admin/login/", admin_login_redirect, name="admin_login_redirect"),
    path("admin/", admin.site.urls),

    # Your app routes
    path("", include("customers.urls")),
    path("", include("accounts.urls")),
]
 