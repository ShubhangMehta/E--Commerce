from tenant_app.orders.models import Order

class CustomerOrderService:
    def list_orders(self, client):
        return Order.objects.filter(client=client)
