from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from tenant_app.orders.models import Order
from tenant_app.orders.serializers.tenant_serializers import TenantOrderSerializer
from tenant_app.orders.serializers.customer_serializers import CustomerOrderSerializer


class OrderListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Tenant → sees all orders
        Customer → sees only their orders
        """
        if request.user.is_staff:
            orders = Order.objects.all()
            serializer = TenantOrderSerializer(orders, many=True)
        else:
            orders = Order.objects.filter(customer=request.user)
            serializer = CustomerOrderSerializer(orders, many=True)

        return Response(serializer.data)


class OrderDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = Order.objects.get(id=pk)

        if request.user.is_staff:
            serializer = TenantOrderSerializer(order)
        else:
            serializer = CustomerOrderSerializer(order)

        return Response(serializer.data)
