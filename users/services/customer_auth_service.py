from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from users.models import CustomerUser

class CustomerAuthService:

    @staticmethod
    def signup(data):
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            password=data["password"]
        )

        CustomerUser.objects.create(
            user=user,   # ⚠️ this requires FK (see note below)
            full_name=data.get("full_name", "")
        )

        return user

    @staticmethod
    def login(email, password):
        user = authenticate(username=email, password=password)
        if not user:
            raise ValueError("Invalid credentials")

        token, _ = Token.objects.get_or_create(user=user)
        return token.key
