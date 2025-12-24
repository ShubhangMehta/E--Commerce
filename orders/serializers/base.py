from rest_framework import serializers
from tenant_app.orders.models import Order

class BaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
