from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta

PLAN_CHOICES = (
    ("Basic", "Basic"),
    ("Standard", "Standard"),
    ("Premium", "Premium"),
)

BILLING_INTERVALS = (
    ("monthly", "Monthly"),
    ("yearly", "Yearly"),
)

class Plan(models.Model):
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    interval = models.CharField(max_length=20, choices=BILLING_INTERVALS, default="monthly")
    amount_in_paise = models.PositiveIntegerField(help_text="e.g. 49900 for ₹499.00")
    razorpay_plan_id = models.CharField(max_length=64, blank=True, null=True, help_text="Optional: map to existing RZP Plan")
    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"

class Subscription(models.Model):
    # tie to your customers.Client once created
    client = models.ForeignKey("customers.Client", on_delete=models.SET_NULL, blank=True, null=True)
    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)   # subdomain without suffix
    email = models.EmailField()

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    started_at = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=30, default="created", choices=(
        ("created", "Created"),
        ("auth_pending", "Auth Pending"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ))

    razorpay_subscription_id = models.CharField(max_length=64, blank=True, null=True, unique=True)
    razorpay_customer_id = models.CharField(max_length=64, blank=True, null=True)

    def mark_period(self, start: timezone.datetime):
        self.current_period_start = start
        if self.plan.interval == "monthly":
            self.current_period_end = start + relativedelta(months=1)
        else:
            self.current_period_end = start + relativedelta(years=1)

class Invoice(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="invoices")
    number = models.CharField(max_length=40, unique=True)
    amount_in_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")
    issued_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=20, default="unpaid", choices=(
        ("unpaid", "Unpaid"),
        ("paid", "Paid"),
        ("refunded", "Refunded"),
    ))
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.number

class Payment(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="payments")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=64, unique=True)
    amount_in_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")
    captured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    meta = models.JSONField(default=dict, blank=True)

class WebhookEvent(models.Model):
    event = models.CharField(max_length=80)
    payload = models.JSONField()
    signature_ok = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

# This is a comment only