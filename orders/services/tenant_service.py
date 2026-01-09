from .order_service import OrderService

class TenantOrderService(OrderService):
    def update_status(self, order, status):
        order.status = status
        order.save()
        return order
