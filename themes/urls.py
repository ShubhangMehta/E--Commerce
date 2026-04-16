from django.urls import path
from . import views
from accounts import views as c_views
from users.views.theme_views import customer_profile
from django.contrib.auth.views import LogoutView
app_name="themes"


urlpatterns = [
    path("", views.index, name="index"),
    #path("signup/", views., name="tenant_customer_signup"),

    path("login/", c_views.login_view, name="login"),
    path("logout/", LogoutView.as_view(next_page="index"), name="logout"),
    path("password_reset/", c_views.forgot_password_view, name="password_reset"),
]
