from django.urls import path
from . import views #, rzp_webhook_views
from django.contrib import admin

urlpatterns=[
    path('',views.home,name='home'),
    path('create-tenant/', views.create_tenant,name='create_tenants'),
    path('raise-ticket/', views.raise_ticket, name='raise_ticket'),
]
