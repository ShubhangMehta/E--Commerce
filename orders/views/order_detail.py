from django.shortcuts import render
from .base import OrderBaseView
from tenant_app.orders.models import Order

class OrderDetailView(OrderBaseView):

    def get(self, request, pk):
        order = Order.objects.get(id=pk)

        template = (
            "orders/tenant/order_detail.html"
            if self.is_tenant(request)
            else "orders/customer/order_detail.html"
        )

        return render(request, template, {"order": order})
