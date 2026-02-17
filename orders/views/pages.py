from django.shortcuts import render, redirect, get_object_or_404
from orders.models import Order
from orders.services.customer_service import CustomerOrderService


class OrderBaseView:
    """
    Base class to determine whether the user is a tenant (admin/staff)
    or a customer.
    """

    def is_tenant(self, request):
        return request.user.is_staff


class OrderCreateView(OrderBaseView):
    """
    Customer-only order creation view
    """

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


class OrderDetailView(OrderBaseView):
    """
    Order detail view for both tenant and customer
    """

    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk)

        template = (
            "orders/tenant/order_detail.html"
            if self.is_tenant(request)
            else "orders/customer/order_detail.html"
        )

        return render(request, template, {"order": order})


class OrderListView(OrderBaseView):
    """
    Order list view for tenant and customer
    """

    def get(self, request):
        if self.is_tenant(request):
            orders = Order.objects.all()
            template = "orders/tenant/order_list.html"
        else:
            orders = Order.objects.filter(customer=request.user)
            template = "orders/customer/order_list.html"

        return render(request, template, {"orders": orders})


@staff_member_required
def invoice_list_view(request):
    """
    Shows all invoices (dashboard/admin dashboard)
    """
    orders = Order.objects.all().order_by("-created_at")

    return render(request, "orders/dashboard/invoices.html", {"orders": orders})