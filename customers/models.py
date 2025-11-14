from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    joined_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
# ---------------------------------------------
#  Subscription Model
# ---------------------------------------------
class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.get_name_display()} - ₹{self.price} ({self.get_status_display()})"
    
# ---------------------------------------------
#  User Subscription (Tracks active plan)
# ---------------------------------------------
class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.get_status_display()})"

# ---------------------------------------------
#  Payment Details
# ---------------------------------------------
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Wallet'),
    ]

    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_PLAN = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_plan = models.CharField(max_length=20, choices=PAYMENT_PLAN, default='monthly')
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.method} - {self.get_status_display()}"
    
# ---------------------------------------------
#  Invoice Model
# ---------------------------------------------
class Invoice(models.Model):
    INVOICE_TYPE = [
        ('manual', 'Manually Generated'),
        ('auto', 'Auto Generated'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE, default='auto')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_invoice_type_display()})"

# ---------------------------------------------
#  Refund / Cancellation Model
# ---------------------------------------------
from django.db import models
from django.contrib.auth.models import User
from .models import Payment  # Make sure Payment model exists

class RefundRequest(models.Model):
    REFUND_TYPES = [
        ('product_issue', 'Product/Service Issue'),
        ('late_delivery', 'Late Delivery'),
        ('payment_error', 'Payment Error'),
        ('duplicate_payment', 'Duplicate Payment'),
        ('subscription_cancel', 'Subscription Cancellation'),
        ('others', 'Others'),
    ]

    REFUND_POLICIES = [
        ('full', 'Full Refund'),
        ('partial', 'Partial Refund'),
        ('no_refund', 'No Refund'),
    ]

    REFUND_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    refund_type = models.CharField(max_length=50, choices=REFUND_TYPES)
    refund_policy = models.CharField(max_length=50, choices=REFUND_POLICIES, default='partial')
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')
    reason = models.TextField()
    terms_and_conditions = models.TextField(default="Refund requests must comply with the platform’s current policy and can be rejected if criteria are not met.")
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    is_refunded = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    policy_version = models.CharField(max_length=10, default="v1.0")

    def __str__(self):
        return f"Refund by {self.user.username} - {self.get_status_display()} ({self.get_refund_type_display()})"

class Client(TenantMixin):
    tenant_name = models.CharField(max_length=100)
    server_name = models.CharField(max_length=150, help_text="VPS or server identifier")
    desired_domain = models.CharField(max_length=150, blank=True, null=True)

    # if you need paid_until, on_trial, created_on, include them here
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)

    auto_create_schema = True  # if you want schemas auto-created

class Domain(DomainMixin):
    pass


