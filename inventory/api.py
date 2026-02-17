from django.urls import path
from .views import StockUpdateAPI

urlpatterns = [
    path("stock/update/", StockUpdateAPI.as_view(), name="stock-update"),
]
