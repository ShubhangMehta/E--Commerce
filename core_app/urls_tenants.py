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
    path("admin/login/", admin_login_redirect, name="admin_login_redirect"),
    path("admin/", admin.site.urls),

    path("", include("accounts.urls")),     # Tenant login/2FA endpoints

    path("", include("themes.urls")),       # Storefront and cart/checkout

    path('catalog/', include('catalog.urls', namespace="catalog")),
    path("", include("orders.urls")),
    path('orders/', include('orders.storefront_urls', namespace="orders_storefront")),
    path('dashboard/', include('dashboard.urls')),  

    path("users/", include("users.urls", namespace="users")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
