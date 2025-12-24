from tenant_app.orders.models import Order
import uuid

class OrderService:

    def create_order(self, client, total_amount):
        return Order.objects.create(
            client=client,
            order_number=str(uuid.uuid4()),
            total_amount=total_amount
        )

    def get_order(self, order_id):
        return Order.objects.get(id=order_id)
