from django.core.exceptions import ValidationError
from django.db import transaction


class CustomerProfileService:

    @staticmethod
    @transaction.atomic
    def update_profile(user, data):
        """
        Update the logged-in user's profile.
        data may contain: full_name, phone
        """

        full_name = data.get("full_name")
        phone = data.get("phone")

        # Update only the fields provided
        if full_name is not None:
            user.full_name = full_name

        if phone is not None:
            user.phone = phone

        user.save()
        return user

    @staticmethod
    def get_profile(user):
        """
        Return only profile-related fields.
        Good for API responses.
        """

        return {
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
        }
