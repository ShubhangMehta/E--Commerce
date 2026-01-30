from rest_framework import serializers
from tenant_app.inventory.models import Stock

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ["id", "product", "quantity", "low_stock_threshold"]
