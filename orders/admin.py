from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "total_amount", "created_at")
    readonly_fields = ("order_number", "total_amount", "created_at")
    inlines = [OrderItemInline]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ["paid", "delivered"]:
            return False
        return True
