"""

from django.contrib import admin
from django.urls import path, include

from customers import views as customer_views

urlpatterns = [
    path('admin/', admin.site.urls),  # FIXED admin URL
    path('', include('accounts.urls')),
    path('', include('customers.urls')),
    path('debug-urls/', customer_views.debug_urls), 
]


"""