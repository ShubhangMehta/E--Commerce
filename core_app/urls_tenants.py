from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # path("", themes_views.index, name="themes_home"),
    path("admin/", admin.site.urls),
    path("", include("catalog.urls")),
    path('', include('themes.urls')),
    path('', include('dashboard.urls')),   
    path("users/", include("users.urls", namespace="users")),
]