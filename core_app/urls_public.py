from django.contrib import admin
<<<<<<< HEAD:core_app/urls_public.py
from django.urls import path,include
#admin.autodiscover()
=======
from django.urls import path, include
>>>>>>> 69fec36 (Razorpay Integration):core_app/urls.py

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
]