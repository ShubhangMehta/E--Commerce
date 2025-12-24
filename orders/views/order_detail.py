from django.shortcuts import render
from tenant_app.orders.models import Order

def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    template = "orders/tenant/order_detail.html" if request.user.is_staff else "orders/customer/order_detail.html"
    return render(request, template, {"order": order})
