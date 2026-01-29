from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import CustomerSignupSerializer, CustomerLoginSerializer 
from users.services.customer_auth_service import CustomerAuthService
class CustomerSignupView(APIView):
    def post(self, request):
        serializer = CustomerSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        CustomerAuthService.signup(serializer.validated_data)

        return Response(
            {"message": "Signup successful"},
            status=status.HTTP_201_CREATED
        )


class CustomerLoginView(APIView):
    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = CustomerAuthService.login(
            serializer.validated_data["email"],
            serializer.validated_data["password"]
        )

        return Response({"token": token})

