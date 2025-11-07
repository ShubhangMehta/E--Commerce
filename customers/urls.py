from django.urls import path
from . import views
from django.contrib import admin

urlpatterns=[
    path('create-tenant/', views.create_tenant, name='create_tenants'),
    path('', views.index, name="index")
]