from tenant_app.orders.models import Order

class CustomerOrderService:
    def create_order(self, tenant, customer, total_amount):
        return Order.objects.create(
            tenant=tenant,
            customer=customer,
            total_amount=total_amount
        )