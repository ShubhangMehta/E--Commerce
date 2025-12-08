from django.urls import path
from . import views

urlpatterns = [
    path("themes/", views.theme_settings, name="theme_settings"),
]

