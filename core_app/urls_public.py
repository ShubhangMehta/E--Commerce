from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme, urlencode

def admin_login_redirect(request):
    next_url = request.GET.get("next", "/index/")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "/login/"
    return redirect("/login/?" + urlencode({"next": next_url}))


urlpatterns = [
    path("admin/login/", admin_login_redirect, name="admin_login_redirect"),
    path("admin/", admin.site.urls),

    path("", include("accounts.urls")),     # Tenant login/2FA endpoints

    path("", include("themes.urls")),

    path('catalogue/', include('catalog.urls')),
    path('', include('themes.urls')),
    path('', include('dashboard.urls')),  
    path('orders/', include('orders.urls')),
    path("users/", include("users.urls")),        
]