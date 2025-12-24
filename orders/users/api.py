from django.urls import path
from users.views.customer_profile import CustomerProfileView

urlpatterns = [
    path("profile/", CustomerProfileView.as_view()),
]
