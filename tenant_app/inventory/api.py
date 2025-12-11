from django.urls import path
from tenant_app.inventory.views.stock_update import StockUpdateAPI

urlpatterns = [
    path("stock/update/", StockUpdateAPI.as_view(), name="stock-update"),
]
