from tenant_app.orders.models import Order

class TenantOrderService:
    def list_orders(self):
        return Order.objects.all()
