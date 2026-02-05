from tenant_app.orders.models import Order

class OrderService:
    def get_order(self, order_id):
        return Order.objects.get(id=order_id)
