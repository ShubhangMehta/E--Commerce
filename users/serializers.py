from rest_framework import serializers
from .models import CustomerUser, CustomerAddress


class CustomerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerUser
        fields = ['id', 'email', 'full_name', 'phone']


class CustomerSignupSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerUser
        fields = ['email', 'full_name', 'phone', 'password']
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        # Hash the password properly
        password = validated_data.pop("password")
        user = CustomerUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = '__all__'
        read_only_fields = ['user']
