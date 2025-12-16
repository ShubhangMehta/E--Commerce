from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

CustomerUser = get_user_model()


class CustomerAuthService:

    @staticmethod
    @transaction.atomic
    def signup(validated_data):
        """
        validated_data should contain:
        email, password, full_name, phone
        """

        email = validated_data.get("email")
        password = validated_data.get("password")
        full_name = validated_data.get("full_name")
        phone = validated_data.get("phone")

        # Email must be unique
        if CustomerUser.objects.filter(email=email).exists():
            raise ValidationError("Email already registered.")

        # Create the user using custom manager
        user = CustomerUser.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
        )

        return user

    @staticmethod
    def login(email, password):
        """
        Authenticate using email-password.
        Returns user if credentials are correct.
        """

        user = authenticate(email=email, password=password)

        if not user:
            raise ValidationError("Invalid email or password.")

        if not user.is_active:
            raise ValidationError("User account is disabled.")

        return user
