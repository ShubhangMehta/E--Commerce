from django.shortcuts import render
from .base import OrderBaseView
from orders.models import Order

class OrderListView(OrderBaseView):

    def get(self, request):
        if self.is_tenant(request):
            orders = Order.objects.all()
            template = "orders/tenant/order_list.html"
        else:
            orders = Order.objects.filter(customer=request.user)
            template = "orders/customer/order_list.html"

        return render(request, template, {"orders": orders})
