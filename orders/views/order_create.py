from django.shortcuts import render, redirect
from tenant_app.orders.services.order_service import OrderService

def order_create(request):
    if request.method == "POST":
        amount = request.POST.get("amount")
        OrderService().create_order(request.user, amount)
        return redirect("order-list")

    return render(request, "orders/customer/order_create.html")
