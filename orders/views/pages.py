from django.shortcuts import render, redirect, get_object_or_404
from orders.models import Order
from django.views import View
from orders.services.order_service import OrderService
from users.views.theme_views import get_subject_member
from users.models import SubjectMember
from themes.views import _theme_path


class OrderBaseView(View):
    """
    Base class to determine whether the user is tenant OWNER
    or a customer.
    """

    def is_owner(self, request):
        subject_member = SubjectMember.objects.get(
            global_user_id=request.user.id
        )
        return subject_member.role == "OWNER"


class OrderDetailView(OrderBaseView):

    def get(self, request, pk):
    
            is_owner = self.is_owner(request)
    
            if is_owner:
                order = get_object_or_404(Order, id=pk)
                template = "orders/dashboard/dashboardorder_detail.html"
            else:
                subject = get_subject_member(request)
                order = get_object_or_404(
                    Order,
                    id=pk,
                    subject=subject  # make sure field name matches
                )
                template = _theme_path(request, "cust_order_detail.html")
    
            return render(request, template, {"order": order})
    
    # ⭐ ADD THIS
    def post(self, request, pk):
        if not self.is_owner(request):
            return redirect("themes:index")

        order = get_object_or_404(Order, id=pk)

        new_status = request.POST.get("status")
        OrderService.update_status(order=order, new_status=new_status)

        return redirect("dashboard_order_detail", pk=pk)


class OrderListView(OrderBaseView):
    """
    Order list view for tenant and customer
    """

    def get(self, request):
        if self.is_owner(request):
            orders = Order.objects.all()
            template = "orders/dashboard/dashboardorder_list.html"
        else:
            subject = get_subject_member(request) 
            orders = Order.objects.filter(subject=subject)
            template = _theme_path(request, "previous_order_listing.html")

        return render(request, template, {"orders": orders})