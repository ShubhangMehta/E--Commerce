from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status

from users.serializers import CoordinateSerializer
from users.services.customer_address_service import AddressService
from users.models import Coordinate, SubjectMember


def get_subject_member(request):
    return SubjectMember.objects.get(
        global_user_id=request.user.id,
        is_active=True
    )


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subject_member = get_subject_member(request)
        addresses = subject_member.addresses.all()
        return Response(
            CoordinateSerializer(addresses, many=True).data
        )

    def post(self, request):
        subject_member = get_subject_member(request)
        AddressService.add_address(subject_member, request.data)
        return Response(
            {"message": "Address added"},
            status=status.HTTP_201_CREATED
        )


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, address_id):
        subject_member = get_subject_member(request)
        address = get_object_or_404(
            Coordinate,
            id=address_id,
            user=subject_member
        )
        AddressService.update_address(address, request.data)
        return Response(
            {"message": "Address updated"},
            status=status.HTTP_200_OK
        )

    def delete(self, request, address_id):
        subject_member = get_subject_member(request)
        address = get_object_or_404(
            Coordinate,
            id=address_id,
            user=subject_member
        )
        AddressService.delete_address(address)
        return Response(
            {"message": "Address deleted"},
            status=status.HTTP_204_NO_CONTENT
        )
