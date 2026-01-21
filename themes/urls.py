from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="store_index"),
    path("products/", views.product_list, name="product_list"),
    path("products/<int:id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("profile/", views.profile, name="profile"),
    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="signup"),
]