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

    path('catalog/', include('catalog.urls',namespace="catalog")),
    path('orders/', include('orders.urls',namespace="orders")),
    path('orders/', include('orders.storefront_urls',namespace="orders_storefront")),
    path('', include('themes.urls')),
    path('', include('dashboard.urls')),  

    #path('', include('users.urls')),

    #path('catalogue/', include('catalog.urls',namespace="catalog")),
    #path('orders/', include('orders.urls',namespace="orders")), 
    path("dashboard/users/", include("users.urls", namespace="users")),
    #path('users/', include('users.theme_urls',namespace="users_theme")),
]

