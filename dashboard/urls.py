from django.urls import path
from . import views
from .api_views import monthly_top_products

app_name = "dashboard"

urlpatterns = [
    path("themes/", views.theme_settings, name="theme_settings"),

    path("", views.dashboard, name="home"),

    # ✅ ONLY ONE API ROUTE
    path("api/monthly-top-products/", monthly_top_products, name="monthly_top_products"),
]