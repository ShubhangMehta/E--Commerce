# users/urls/theme_urls.py
from django.urls import path
from users.views import theme_views

app_name = "users_theme"

urlpatterns = [
    path('profile/', theme_views.customer_profile, name='profile'),
    path('address/', theme_views.customer_address, name='address'),
]
