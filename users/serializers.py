from rest_framework import serializers
from .models import SubjectMember, Coordinate


class SubjectMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for tenant-scoped users.
    This does NOT handle authentication.
    """

    class Meta:
        model = SubjectMember
        fields = [
            "id",
            "global_user_id",
            "email",
            "full_name",
            "phone",
            "role",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "global_user_id",
            "created_at",
        ]


class CoordinateSerializer(serializers.ModelSerializer):
    """
    Serializer for tenant-scoped addresses.
    """

    class Meta:
        model = Coordinate
        fields = [
            "id",
            "user",
            "full_name",
            "phone",
            "house_no",
            "landmark",
            "city",
            "state",
            "postal_code",
            "address_type",
            "is_default",
        ]
        read_only_fields = [
            "id",
            "user",
        ]
