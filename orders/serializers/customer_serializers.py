from rest_framework import serializers
class CustomerOrderSerializer(serializers.Serializer):
    class Meta(serializers.Serializer):
        read_only_fields = ("status", "tenant")
