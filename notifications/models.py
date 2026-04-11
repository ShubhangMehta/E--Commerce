from turtle import mode

from django.db import models
from orders.models import Order
from payments.models import OrderPayment

# Create your models here.
class EmailNotification(models.Model):
    event = models.CharField(max_length=100) #order_paid
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(OrderPayment, on_delete=models.CASCADE)

    to_email = models.EmailField()
    subject = models.CharField(max_length=255)

    status = models.CharField(max_length=20, default="pending") # pending, sent, failed
    error_message = models.TextField(blank=True)
    payload_snapshot = models.JSONField(default=dict, blank=True) # Store the payload that triggered this notification
    sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "order", "payment"],
                name="uniq_order_paid_email_per_payment",
            )
        ]
        