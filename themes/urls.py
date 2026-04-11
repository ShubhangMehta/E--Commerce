from django.urls import path
from . import views
from accounts import views as c_views

urlpatterns = [
    path("", views.index, name="index"),
    #path("signup/", views., name="tenant_customer_signup"),

    path("login/", c_views.login_view, name="login"),
    path("password_reset/", c_views.forgot_password_view, name="password_reset"),
]
