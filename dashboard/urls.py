from django.urls import path
from . import views
from .api_views import monthly_top_products
#from customers import views as customers_views


app_name = "dashboard"

urlpatterns = [
    path("themes/", views.theme_settings, name="theme_settings"),

    #Razorpay Payment Urls; Just used simple names here easy to comprehend and change later if needed

    path('', views.dashboard, name='home'),
    


    path("api/monthly-top-products/", monthly_top_products, name="monthly_top_products"),

    
]
