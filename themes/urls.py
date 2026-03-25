from django.urls import path
from . import views
from accounts import views as c_views
from django.contrib.auth import views as auth_views
from users.views.theme_views import customer_profile



urlpatterns = [
    path("", views.index, name="index"),

    #path("products/", views.product_list, name="product_list"),

    # IMPORTANT: your template uses product_detail, keep URL name as "product_detail"
    # and keep the same <int:id> param your views already use.
    #path("products/<int:id>/", views.product_detail, name="product_detail"),

    # Cart
    # path("cart/", views.cart, name="cart"),
    # path("cart/update/", views.cart_update, name="cart_update"),
    # path("cart/remove/", views.cart_remove, name="cart_remove"),

    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="tenant_customer_signup"),

    path("login/", c_views.login_view, name="login"),
    path("password_reset/", c_views.forgot_password_view, name="password_reset"),
    

]
