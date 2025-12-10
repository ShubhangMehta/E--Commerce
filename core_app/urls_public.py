from django.contrib import admin
<<<<<<< HEAD:core_app/urls_public.py
from django.urls import path,include
#admin.autodiscover()
=======
from django.urls import path, include
<<<<<<< HEAD:core_app/urls_public.py
>>>>>>> 69fec36 (Razorpay Integration):core_app/urls.py
=======
from customers.views import home
>>>>>>> 304533d (cleaned the unwanted files and folders):core_app/urls.py

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="public_home"),
    path("", include("accounts.urls")),
    path("", include("customers.urls")),
]
