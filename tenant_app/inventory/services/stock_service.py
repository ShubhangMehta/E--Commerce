from tenant_app.inventory.models import Stock

class StockService:

    def get_stock(self, product):
        return Stock.objects.get(product=product)

    def increase_stock(self, product, amount):
        stock = self.get_stock(product)
        stock.quantity += amount
        stock.save()
        return stock

    def decrease_stock(self, product, amount):
        stock = self.get_stock(product)
        if stock.quantity < amount:
            raise ValueError("Insufficient stock!")
        stock.quantity -= amount
        stock.save()
        return stock
