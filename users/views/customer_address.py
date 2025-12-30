from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from users.serializers import CustomerAddressSerializer
from users.services.customer_address_service import CustomerAddressService
from users.models import CustomerAddress

class CustomerAddressListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = request.user.addresses.all()
        return Response(CustomerAddressSerializer(addresses, many=True).data)

    def post(self, request):
        CustomerAddressService.add_address(request.user, request.data)
        return Response({"message": "Address added"}, status=status.HTTP_201_CREATED)


class CustomerAddressDetail(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, address_id):
        address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
        CustomerAddressService.update_address(address, request.data)
        return Response({"message": "Address updated"}, status=status.HTTP_200_OK)

    def delete(self, request, address_id):
        address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
        CustomerAddressService.delete_address(address)
        return Response({"message": "Address deleted"}, status=status.HTTP_204_NO_CONTENT)
