from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils import timezone
from .models import SubscriptionPlan  # assuming SubscriptionPlan is in the same app

class Client(TenantMixin):
    tenant_name = models.CharField(max_length=100)
    server_name = models.CharField(max_length=150, help_text="VPS or server identifier")
    desired_domain = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    # Subscription info
    subscription_plan = models.ForeignKey(
        'SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True
    )
    subscription_start = models.DateField(null=True, blank=True)
    subscription_end = models.DateField(null=True, blank=True)
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')

    # Usage & Analytics
    storage_used_mb = models.FloatField(default=0.0)
    product_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    visitor_count_7d = models.IntegerField(default=0)
    visitor_count_30d = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)

    auto_create_schema = True

    def __str__(self):
        return self.tenant_name

    
class Domain(DomainMixin):
    pass
class TenantRequest(models.Model):
    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    PAYMENT_METHODS = [
        ('COD', 'Cash On Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='COD')

    PAYMENT_PLANS = [
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
    ]
    payment_plan = models.CharField(max_length=10, choices=PAYMENT_PLANS, default='Monthly')

    created_on = models.DateTimeField(auto_now_add=True)
    requested_on = models.DateField(default=timezone.now)
    is_approved = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.tenant_name} ({self.status})"
    
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
    storage_limit_mb = models.PositiveIntegerField(default=500)  # Feature: storage per plan
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.get_name_display()} - ₹{self.price} ({self.get_status_display()})"
    
# ---------------------------------------------
#  Client Subscription (Tracks active plan)
# ---------------------------------------------
class ClientSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    duration_days = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    grace_period_days = models.PositiveIntegerField(default=3)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    manual_override = models.BooleanField(
        default=False,
        help_text="If enabled, admin can manually modify subscription dates or status."
    )
    payment_reference = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Reference to the payment transaction for this subscription."
    )

    def save(self, *args, **kwargs):
        if not self.manual_override:
            # Set subscription dates
            if not self.start_date:
                self.start_date = timezone.now()
            if self.plan and not self.end_date:
                self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
            
            # Update status based on dates
            current_time = timezone.now()
            if self.end_date and self.end_date < current_time:
                self.status = 'expired'
            elif self.status not in ['suspended', 'cancelled']:
                self.status = 'active'

            # Set client status based on subscription
            self.client.status = 'Active' if self.status == 'active' else 'Suspended'

            # Copy plan-specific storage to client
            if self.plan:
                self.client.storage_used_mb = self.plan.storage_limit_mb

            # Save the client to apply updates
            self.client.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.tenant_name} - {self.plan.name if self.plan else 'No Plan'} ({self.status})"

# ---------------------------------------------
#  Payment Details
# ---------------------------------------------
class Payment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=20, choices=TenantRequest.PAYMENT_METHODS)
    payment_plan = models.CharField(max_length=20, choices=TenantRequest.PAYMENT_PLANS)
    transaction_id = models.CharField(max_length=100, unique=True)
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Wallet'),
    ]

    status_choices = [
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

    status = models.CharField(max_length=20, choices=status_choices, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.tenant_name} - {self.method} - {self.status}"

    
# ---------------------------------------------
#  Invoice Model
# ---------------------------------------------
class Invoice(models.Model):
    INVOICE_TYPE = [
        ('manual', 'Manually Generated'),
        ('auto', 'Auto Generated'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE)
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

    client = models.ForeignKey(User, on_delete=models.CASCADE)
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




