from django_tenants.utils import schema_context
from models import Client
from catalog.models import Product
from orders.models import Order


class ClientAnalyticsService:

    @staticmethod
    def update_client_stats(client):
        with schema_context(client.schema_name):
            product_count = Product.objects.count()
            order_count = Order.objects.count()

        client.product_count = product_count
        client.order_count = order_count
        client.save()

    @staticmethod
    def update_all_clients():
        for client in Client.objects.all():
            ClientAnalyticsService.update_client_stats(client)