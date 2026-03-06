from django.contrib import admin
from orders.models import Order, OrderItem

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "tenant",
#         "subject",
#         "total_amount",
#         "status",
#         "created_at",
#     )
#     list_filter = ("status", "created_at", "tenant")
#     search_fields = ("id", "subject__user__username", "tenant")
#     ordering = ("-created_at",)

# @admin.register(OrderItem)
# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "order",
#         "product_name",
#         "quantity",
#         "product_price",
#         "line_total",
#     )
#     search_fields = ("product_name", "order__id")
#     list_filter = ("order__status",)
