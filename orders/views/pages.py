from django.shortcuts import render, redirect, get_object_or_404
from orders.models import Order
from django.views import View
from orders.services.order_service import OrderService
from users.views.theme_views import get_subject_member


class OrderBaseView(View):
    """
    Base class to determine whether the user is a tenant (admin/staff)
    or a customer.
    """

    def is_tenant(self, request):
        return request.user.is_staff


#class OrderCreateView(OrderBaseView):
#    """
#    Customer-only order creation view
#    """
#
#    def get(self, request):
#        return render(request, "orders/customer/order_create.html")
#
#    def post(self, request):
#        service = CustomerOrderService()
#        service.create_order(
#            tenant="default_tenant",
#            customer=request.user,
#            total_amount=request.POST.get("amount")
#        )
#        return redirect("order-list")


class OrderDetailView(OrderBaseView):

    def get(self, request, pk):
        if self.is_tenant(request):
            order = get_object_or_404(Order, id=pk)
        else:
            subject = get_subject_member(request)
            order = get_object_or_404(Order, id=pk, subject=subject)

        template = (
            "orders/dashboard/dashboardorder_detail.html"
            #if self.is_tenant(request)
            #else "orders/customer/order_detail.html"
        )

        return render(request, template, {"order": order})

    # ⭐ ADD THIS
    def post(self, request, pk):
        #if not self.is_tenant(request):
            #return redirect("storefront")

        order = get_object_or_404(Order, id=pk)

        new_status = request.POST.get("status")
        OrderService.update_status(order=order, new_status=new_status)

        return redirect("orders:dashboard_order_detail", pk=pk)


class OrderListView(OrderBaseView):
    """
    Order list view for tenant and customer
    """

    def get(self, request):
        #if self.is_tenant(request):
        orders = Order.objects.all()
        template = "orders/dashboard/dashboardorder_list.html"
        #else:
            #orders = Order.objects.filter(customer=request.user)
            #template = "orders/customer/order_list.html"

        return render(request, template, {"orders": orders})