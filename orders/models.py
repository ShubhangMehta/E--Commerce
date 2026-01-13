# from django.db import models
# from django.contrib.auth.models import User

# class Order(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('paid', 'Paid'),
#         ('shipped', 'Shipped'),
#         ('delivered', 'Delivered'),
#         ('cancelled', 'Cancelled'),
#     ]

#     client = models.ForeignKey(User, on_delete=models.CASCADE)
#     order_number = models.CharField(max_length=50, unique=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.order_number

# class Order(models.Model):
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=50, default='Pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order {self.order_number} - {self.customer_name}"
    






from django.db import models
from django.contrib.auth.models import User
import uuid


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # AUTO generate order number
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

# order
class OrderItem(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ("electronics", "Electronics"),
        ("fashion", "Fashion"),
        ("grocery", "Grocery"),
    ]

    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPE_CHOICES)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()
    product_image = models.ImageField(upload_to="products/", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_order_total()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.update_order_total()

    def update_order_total(self):
        total = sum(item.get_total_price() for item in self.order.items.all())
        self.order.total_amount = total
        self.order.save(update_fields=["total_amount"])
