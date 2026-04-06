from django.db import models
from catalog.models import SingleProduct

class Stock(models.Model):
    product = models.OneToOneField(SingleProduct, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"