from django.urls import path, include

urlpatterns = [
    path("", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("", include("orders.urls")),
    path("", include("themes.urls")),
]
