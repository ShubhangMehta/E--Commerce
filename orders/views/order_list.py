from django.shortcuts import render
from tenant_app.orders.services.customer_service import CustomerOrderService
from tenant_app.orders.services.tenant_service import TenantOrderService

def order_list(request):
    if request.user.is_staff:
        orders = TenantOrderService().list_orders()
        template = "orders/tenant/order_list.html"
    else:
        orders = CustomerOrderService().list_orders(request.user)
        template = "orders/customer/order_list.html"

    return render(request, template, {"orders": orders})
