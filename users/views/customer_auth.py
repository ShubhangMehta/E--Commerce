from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users import serializers, services

class CustomerSignupView(APIView):
    def post(self, request):
        serializer = serializers.CustomerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.CustomerAuthService.signup(serializer.validated_data)
        return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)


class CustomerLoginView(APIView):
    def post(self, request):
        serializer = serializers.CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        token = services.CustomerAuthService.login(email, password)
        return Response({"token": token}, status=status.HTTP_200_OK)
