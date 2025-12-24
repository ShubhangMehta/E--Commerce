from rest_framework.views import APIView
from rest_framework.response import Response

class CustomerAuthView(APIView):
    def post(self, request):
        return Response({"message": "Auth success"})
