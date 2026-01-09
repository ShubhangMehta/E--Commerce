from rest_framework import serializers
from .models import SingleProduct


class SingleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleProduct
        fields = [
            "id",
            "brand_name",
            "name",
            "price",
            "description",
            "availability",
            "seller",
            "estimated_delivery",
            "refundable",
            "returnable",
        ]
