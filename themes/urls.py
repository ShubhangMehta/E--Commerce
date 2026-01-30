from django.urls import path
from . import views

urlpatterns = [
    #path("", views.index, name="store_index"),
    path("products/", views.product_list, name="product_list"),

    # IMPORTANT: your template uses product_detail, keep URL name as "product_detail"
    # and keep the same <int:id> param your views already use.
    path("products/<int:id>/", views.product_detail, name="product_detail"),

    # Cart
    path("cart/", views.cart, name="cart"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),

    # Checkout + order success
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/", views.order_success, name="order_success"),

    # Profile + orders history
    path("profile/", views.profile, name="profile"),
    path("orders/", views.previous_order_listing, name="previous_order_listing"),

    # Auth pages (signup view you added; login/logout can stay in accounts app)
    path("signup/", views.signup, name="signup"),

    path("index",views.index,name="index"),
]
