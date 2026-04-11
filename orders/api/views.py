from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from orders.models import Order
from orders.serializers.serializers import StartPaymentSerializer
from orders.services.payment_start import RazorpayGatewayError, create_razorpay_order_for_order

from orders.serializers.tenant_serializers import TenantOrderSerializer
from orders.serializers.customer_serializers import CustomerOrderSerializer
from users.views.customer_profile import get_subject_member

class StartPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        serializer = StartPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(Order, id=order_id, subject=request.subject_member) #use your tenant member identity here

        if order.payment_status == "paid":
            return Response({"detail": "Order is already paid."}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.status == "cancelled":
            return Response({"detail": "Cannot start payment for a cancelled order."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rp_order = create_razorpay_order_for_order(tenant=request.tenant, order=order)
        except RazorpayGatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            "key": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": rp_order["id"],
            "amount": rp_order["amount"],
            "currency": rp_order["currency"],
            "local_order_id": order.id,
            "local_order_number": str(order.id),
            "customer_email": order.customer_email,
            "customer_name": order.customer_name,
            }, status=status.HTTP_200_OK
        )
  

class OrderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        subject = get_subject_member(request)
    
        order = get_object_or_404(Order, id=order_id, subject=subject)

        return Response({
            "order_id": order.id,
            "payment_status": order.payment_status,
            "status": order.status,
        })


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
