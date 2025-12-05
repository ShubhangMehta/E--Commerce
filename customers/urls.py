from django.urls import path
from . import views
from django.contrib import admin

urlpatterns=[
    path('create-tenant/', views.create_tenant,name='create_tenants'),
    path("admin/", admin.site.urls),
    path('',views.home,name="home"),
    path('raise-ticket/', views.raise_ticket, name='raise_ticket')
]