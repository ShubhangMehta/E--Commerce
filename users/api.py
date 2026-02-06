from django.urls import path
#from users.views.customer_auth import CustomerSignupView, CustomerLoginView
from users.views.customer_profile import ProfileView
from users.views.customer_address import AddressListCreateView, AddressDetailView

urlpatterns = [
    #path("auth/signup/", CustomerSignupView.as_view()),
    #path("auth/login/", CustomerLoginView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("addresses/", AddressListCreateView.as_view()),
    path("addresses/<int:address_id>/", AddressDetailView.as_view()),
]
