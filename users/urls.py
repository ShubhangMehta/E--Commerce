from django.urls import path, include
from .views_profile import profile_view, address_add, address_edit, address_delete, tenant_customer_signup, users_home
from users.views import theme_views

app_name="users"


urlpatterns = [
    path("", users_home, name="list"),
    # path("api/", include("users.api")),
    # path('profile/', theme_views.customer_profile, name='profile'),
    # path('address/', theme_views.customer_address, name='address'),
    path("customer/signup", tenant_customer_signup, name="tenant_customer_signup"),
    
    path("profile/", profile_view, name="profile"),
    path("profile/address/add/", address_add, name="address_add"),
    path("profile/address/<int:address_id>/edit/", address_edit, name="address_edit"),
    path("profile/address/<int:address_id>/delete/", address_delete, name="address_delete"),

]

