from django.urls import path
from . import views
from accounts import views as c_views
from django.contrib.auth import views as auth_views
from users.views.theme_views import customer_profile

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.signup, name="tenant_customer_signup"),

    path("login/", c_views.login_view, name="login"),
    #path("orders/invoice/<int:order_id>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("password_reset/", c_views.forgot_password_view, name="password_reset"),
]
