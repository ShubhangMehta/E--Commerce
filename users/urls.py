from django.urls import path, include
from users.views.pages import users_home
from users.views.views_auth import tenant_customer_signup
from users.views import theme_views

app_name = "users"

urlpatterns = [
    path("", users_home, name="list"),
    path("api/", include("users.api")),
    path("user/signup", tenant_customer_signup, name="tenant_customer_signup"),
    path('profile/', theme_views.customer_profile, name='profile'),
    path('address/', theme_views.customer_address, name='address'),
]
