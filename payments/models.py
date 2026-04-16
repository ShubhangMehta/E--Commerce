from django.db import models
from orders.models import Order
# Create your models here.

class OrderPayment(models.Model):
    order = models.ForeignKey(Order, related_name="payments", on_delete=models.CASCADE)

    razorpay_order_id = models.CharField(max_length=100, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, db_index=True, unique=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=30, default="captured")  # captured, failed, pending
    payment_method = models.CharField(max_length=50, default="razorpay", blank=True)  # razorpay, cod, wallet, etc.
    currency = models.CharField(max_length=10, default="INR")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    paid_at = models.DateTimeField(blank=True, null=True)
    raw_payload = models.JSONField(default=dict, blank=True)  # Store the entire payload for future reference

    confirmation_email_sent = models.BooleanField(default=False)
    confirmation_email_sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
