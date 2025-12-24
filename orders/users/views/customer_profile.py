from rest_framework.views import APIView
from rest_framework.response import Response
from users.models import CustomerProfile

class CustomerProfileView(APIView):
    def get(self, request):
        profile = CustomerProfile.objects.get(user=request.user)
        return Response({"phone": profile.phone})
