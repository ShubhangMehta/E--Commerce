from tenant_app.inventory.models import Stock


class StockUpdateService:

    def update(self, product, quantity):
        stock = Stock.objects.get(product=product)
        stock.quantity = quantity
        stock.save()
        return stock
