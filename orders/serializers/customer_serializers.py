from serializers import BaseOrderSerializer

class CustomerOrderSerializer(BaseOrderSerializer):
    class Meta(BaseOrderSerializer.Meta):
        read_only_fields = ("status", "tenant")

class CustomerOrderSerializer(BaseOrderSerializer):
    pass

