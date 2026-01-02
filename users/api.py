from django.urls import path
from users.views.customer_auth import CustomerSignupView, CustomerLoginView
from users.views.customer_profile import CustomerProfileView
from users.views.customer_address import CustomerAddressListCreate, CustomerAddressDetail

urlpatterns = [
    path("auth/signup/", CustomerSignupView.as_view()),
    path("auth/login/", CustomerLoginView.as_view()),
    path("profile/", CustomerProfileView.as_view()),
    path("addresses/", CustomerAddressListCreate.as_view()),
    path("addresses/<int:address_id>/", CustomerAddressDetail.as_view()),
]
