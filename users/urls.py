from django.urls import path, include
from . import views_profile

app_name="users"


urlpatterns = [
    path("", views_profile.users_home, name="list"),
    # path("api/", include("users.api")),
    #path('profile/', theme_views.customer_profile, name='profile'),
    #path('address/', theme_views.customer_address, name='address'),
    path("signup", views_profile.tenant_customer_signup, name="users:tenant_customer_signup"),
    
    path("profile/", views_profile.profile_view, name="profile"),
    path("profile/address/add/", views_profile.address_add, name="address_add"),
    path("profile/address/<int:address_id>/edit/", views_profile.address_edit, name="address_edit"),
    path("profile/address/<int:address_id>/delete/", views_profile.address_delete, name="address_delete"),

    
    path("staff/", views_profile.staff_list, name="staff_list"),
    path("staff/invite/", views_profile.staff_invite_view, name="staff_invite_create"),
    path("staff/accept/<uuid:token>/", views_profile.staff_invite_accept, name="staff_invite_accept"),
    path("staff/invite/<uuid:token>/revoke/", views_profile.staff_invite_revoke, name="staff_invite_revoke"),
    path("staff/<int:member_id>/deactivate/", views_profile.staff_deactivate, name="staff_deactivate"),

]

