from django.db import models
from tenant_app.inventory.models import Product

class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"
