from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    tenant = models.CharField(max_length=100, default="default")  # tenant schema or tenant name
    customer = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"

#class Order(models.Model):
#    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#    status = models.CharField(max_length=50, default='Pending')
#    created_at = models.DateTimeField(auto_now_add=True)
#
#    def __str__(self):
#        return f"Order {self.order_number} - {self.customer_name}"