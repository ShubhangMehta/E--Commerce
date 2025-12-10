from django.contrib import admin
from django.urls import path, include
from customers.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="public_home"),
    path("", include("accounts.urls")),
    path("", include("customers.urls")),
]
