from django.shortcuts import render, redirect
from .base import OrderBaseView
from orders.services.customer_service import CustomerOrderService

class OrderCreateView(OrderBaseView):

    def get(self, request):
        return render(request, "orders/customer/order_create.html")

    def post(self, request):
        service = CustomerOrderService()
        service.create_order(
            tenant="default_tenant",
            customer=request.user,
            total_amount=request.POST.get("amount")
        )
        return redirect("order-list")