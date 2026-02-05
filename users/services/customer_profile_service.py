from django.db import transaction


class ProfileService:

    @staticmethod
    @transaction.atomic
    def update_profile(subject_member, data):
        """
        Update the customer's profile (tenant-scoped).
        Allowed fields: full_name, phone
        """

        if "full_name" in data:
            subject_member.full_name = data["full_name"]

        if "phone" in data:
            subject_member.phone = data["phone"]

        subject_member.save()
        return subject_member

    @staticmethod
    def get_profile(subject_member):
        """
        Return customer profile fields.
        """
        return {
            "email": subject_member.email,
            "full_name": subject_member.full_name,
            "phone": subject_member.phone,
        }
