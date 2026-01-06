from django.urls import path, include
from themes import views as themes_views
from dashboard import views as dashboard_views



urlpatterns = [
    path("", themes_views.index, name="themes_home"),
    #storefront dashboard
    path("products/", themes_views.product_list, name="product_list"),
    path("products/<int:id>/", themes_views.product_detail, name="product_detail"),

     #tenant admin/dashboard
    path("dashboard/", dashboard_views.dashboard_home, name="dashboard_home"),
    path("dashboard/products/", dashboard_views.products, name="dashboard_products"),
    path("dashboard/themes/", dashboard_views.themes, name="dashboard_themes"),
    path('', include('themes.urls')),
    path('', include('dashboard.urls')),   
]