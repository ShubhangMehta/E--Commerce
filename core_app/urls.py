from django.contrib import admin
from django.urls import path,include
#admin.autodiscover()
urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('customers.urls')),
    #path("users/", include("users.urls")),
    path('dashboard/', include('dashboard.urls')),
    path('users/', include('users.urls',namespace="users")),
    #path('orders/', include('orders.urls',namespace="orders")),
    path('catalog/', include('catalog.urls',namespace="catalog")),

]
