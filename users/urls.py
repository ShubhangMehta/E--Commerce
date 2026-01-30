from django.urls import path, include
from users.views.pages import users_home

app_name = "users"

urlpatterns = [
    path("", users_home, name="list"),
    path("api/", include("users.api")),
]

