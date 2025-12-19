from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Create your models here.

class Client(TenantMixin):
    tenant_name = models.CharField(max_length=100)
    server_name = models.CharField(max_length=150, help_text="VPS or server identifier")
    desired_domain = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    theme = models.CharField(max_length=50, default='default', help_text="Theme or template name for the tenant")
    has_used_trial = models.BooleanField(default=False)

    # Usage & Analytics
    storage_used_mb = models.FloatField(default=0.0)
    product_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    visitor_count_7d = models.IntegerField(default=0)
    visitor_count_30d = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)

    auto_create_schema = True

   # STATUS_CHOICES = [
    #    ('Active', 'Active'),
     #   ('Suspended', 'Suspended'),
    #]

    @property
    def status(self):
        """Returns current client status based on latest subscription."""
        latest_subscription = self.clientsubscription_set.order_by('-end_date').first()
        if not latest_subscription:
            return 'Inactive'
        return 'Active' if latest_subscription.status == 'active' else 'Suspended'

    @property
    def current_plan(self):
        """Returns the latest plan name or None."""
        latest_subscription = self.clientsubscription_set.order_by('-end_date').first()
        if not latest_subscription or not latest_subscription.plan:
            return None
        return latest_subscription.plan.name

    @property
    def subscription_start(self):
        """Returns start date of latest subscription."""
        latest_subscription = self.clientsubscription_set.order_by('-end_date').first()
        if not latest_subscription:
            return None
        return latest_subscription.start_date

    @property
    def subscription_end(self):
        """Returns end date of latest subscription."""
        latest_subscription = self.clientsubscription_set.order_by('-end_date').first()
        if not latest_subscription:
            return None
        return latest_subscription.end_date

    def __str__(self):
        return self.tenant_name
    @property
    def created_on(self):
        latest_sub = self.clientsubscription_set.order_by('-start_date').first()
        return latest_sub.start_date.date() if latest_sub else None
    
class Domain(DomainMixin):
    pass


# ---------------------------------------------
#  Subscription Model
# ---------------------------------------------

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('free_trial', 'Free Trial'),
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
    is_trial = models.BooleanField(default=False)
    storage_limit_mb = models.PositiveIntegerField(default=500)  # Feature: storage per plan
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        label = "🆓 Trial" if self.is_trial else "💳 Paid"
        return f"{self.get_name_display()} ({label})"
    
class PlanPricing(models.Model):
    BILLING_CHOICES = [
        ('trial', 'Free Trial'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_trial = models.BooleanField(default=False)

    class Meta:
        unique_together = ('plan', 'billing_cycle')

    def __str__(self):
        return f"{self.plan} - {self.get_billing_cycle_display()}"
    def clean(self):
        if self.billing_cycle == 'trial' and not self.plan.is_trial:
            raise ValidationError("Only trial plans can have trial billing cycle")


class TenantRequest(models.Model):
    """
    Stores sign-up requests from businesses wanting to create a tenant.
    """

    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    pricing = models.ForeignKey(PlanPricing,on_delete=models.PROTECT,null=True,blank=True)

    THEME_CHOICES = [
        ('default', 'Default'),
        ('minimal', 'Minimal'),
        ('modern', 'Modern'),
    ]

    theme = models.CharField(
        max_length=50,
        choices=THEME_CHOICES,
        default='default'
    )
    
    PAYMENT_PLANS = [
        ('Monthly', 'Monthly'), #499 999 1999
        ('Yearly', 'Yearly'), 
    ]
    payment_plan = models.CharField(max_length=10, choices=PAYMENT_PLANS, default='Monthly')

    created_on = models.DateTimeField(auto_now_add=True)
    requested_on = models.DateField(default=timezone.now)
    is_approved = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    def __str__(self):
        return f"{self.tenant_name} ({self.status})"


class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical Issue'),
        ('billing', 'Billing'),
        ('general', 'General Query'),
        ('feature', 'Feature Request'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    assigned_to = models.CharField(max_length=255, null=True, blank=True)  # could be staff username or email
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# ---------------------------------------------
#  Payment Details
# ---------------------------------------------
class Payment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_plan = models.CharField(max_length=20, choices=TenantRequest.PAYMENT_PLANS)
    transaction_id = models.CharField(max_length=100, unique=True)
    status_choices = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.tenant_name} - {self.payment_plan} - {self.status}"
    
# ---------------------------------------------
#  Client Subscription (Tracks active plan)
# ---------------------------------------------
class ClientSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]

    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True)
    pricing = models.ForeignKey(PlanPricing,on_delete=models.PROTECT,null=True,blank=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    manual_override = models.BooleanField(
        default=False,
        help_text="If enabled, admin can manually modify subscription dates or status."
    )

    class Meta:
        ordering = ['-end_date']  # Latest subscription first

    def save(self, *args, **kwargs):
        if not self.manual_override:
            # Set subscription start and end dates if not provided
            if not self.start_date:
                self.start_date = timezone.now()
            if self.pricing and not self.end_date:
                self.end_date = self.start_date + timedelta(days=self.pricing.duration_days)

            # Update subscription status based on current date
            now = timezone.now()
            if self.status not in ['suspended', 'cancelled']:
                if self.end_date and self.end_date < now:
                    self.status = 'expired'
                else:
                    self.status = 'active'

        super().save(*args, **kwargs)

    def __str__(self):
        plan_name = self.plan.name if self.plan else 'No Plan'
        return f"{self.client.tenant_name} - {plan_name} ({self.status})"
    
# ---------------------------------------------
#  Invoice Model
# ---------------------------------------------
class Invoice(models.Model):
    INVOICE_TYPE = [
        ('manual', 'Manually Generated'),
        ('auto', 'Auto Generated'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    subscription = models.ForeignKey(ClientSubscription, on_delete=models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE, default='auto')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_invoice_type_display()})"

# ---------------------------------------------
#  Refund / Cancellation Model
# ---------------------------------------------

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

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
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
        return f"Refund by {self.client.tenant_name} - {self.get_status_display()} ({self.get_refund_type_display()})"

# ================================================================
#   RAZORPAY BILLING MODELS
# ================================================================

# PLAN_CHOICES = (
#     ('basic', 'Basic'),
#     ('standard', 'Standard'),
#     ('premium', 'Premium'),
# )

# BILLING_INTERVALS = (
#     ('monthly', 'Monthly'),
#     ('yearly', 'Yearly'),
# )

# class RzpPlan(models.Model):
#     """
#     Razorpay plan created for automated billing.
#     """

#     name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
#     interval = models.CharField(max_length=20, choices=BILLING_INTERVALS, default="monthly")

#     amount_in_paise = models.PositiveIntegerField(
#         help_text="100.00 INR → 10000 paise"
#     )

#     razorpay_plan_id = models.CharField(
#         max_length=64, blank=True, null=True, help_text="Maps to an existing RZP plan if needed"
#     )

#     features = models.JSONField(default=dict, blank=True)

#     def __str__(self):
#         return f"{self.name} ({self.interval})"


# class RzpSubscription(models.Model):

#     client = models.ForeignKey(
#         "customers.Client", on_delete=models.SET_NULL, blank=True, null=True
#     )

#     tenant_name = models.CharField(max_length=100)
#     desired_domain = models.CharField(max_length=150)
#     email = models.EmailField()

#     # ⭐ ADD THESE TWO FIELDS
#     brand_color = models.CharField(max_length=20, default="#000000")
#     theme = models.CharField(max_length=50, default="default")


#     plan = models.ForeignKey(RzpPlan, on_delete=models.PROTECT)
#     interval = models.CharField(max_length=20, choices=BILLING_INTERVALS, default="monthly")

#     status = models.CharField(
#         max_length=20,
#         choices=[
#             ("created", "Created"),
#             ("active", "Active"),
#             ("pending", "Pending"),
#             ("past_due", "Past Due"),
#             ("cancelled", "Cancelled"),
#             ("expired", "Expired"),
#         ],
#         default="created"
#     )

#     razorpay_subscription_id = models.CharField(max_length=64, unique=True, blank=True, null=True)

#     started_at = models.DateTimeField(blank=True, null=True)
#     current_period_start = models.DateTimeField(blank=True, null=True)
#     current_period_end = models.DateTimeField(blank=True, null=True)
#     cancel_at_period_end = models.BooleanField(default=False)
#     cancelled_at = models.DateTimeField(blank=True, null=True)

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.email} - {self.plan.name} ({self.status})"


# class RzpInvoice(models.Model):
#     """
#     Razorpay invoice created for subscription billing.
#     """

#     subscription = models.ForeignKey(RzpSubscription, on_delete=models.CASCADE, related_name="invoices")

#     invoice_number = models.CharField(max_length=50, unique=True)
#     amount_in_paise = models.PositiveIntegerField()
#     currency = models.CharField(max_length=10, default="INR")

#     status = models.CharField(
#         max_length=20,
#         choices=[("pending", "Pending"), ("paid", "Paid"), ("refunded", "Refunded")],
#         default="pending"
#     )

#     due_date = models.DateTimeField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     paid_at = models.DateTimeField(blank=True, null=True)

#     def __str__(self):
#         return self.invoice_number

class RzpPayment(models.Model):
    """
    Razorpay payment for a subscription invoice.
    """

    subscription = models.ForeignKey(ClientSubscription, on_delete=models.CASCADE, related_name="payments")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True)

    razorpay_payment_id = models.CharField(max_length=64, unique=True)
    amount= models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")

    captured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    meta = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.razorpay_payment_id


class RzpWebhookEvent(models.Model):
    """
    Stores webhook events received from Razorpay.
    Used for validating and syncing payment states.
    """

    event = models.CharField(max_length=80)
    payload = models.JSONField()
    signature_ok = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event} @ {self.received_at}"


class RzpRefund(models.Model):
    """
    Razorpay refund for a payment transaction.
    """

    payment = models.ForeignKey(RzpPayment, on_delete=models.CASCADE, related_name="refunds")

    razorpay_refund_id = models.CharField(max_length=64, unique=True)
    amount_in_paise = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunded_approvals",
    )
    approved_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Refund {self.id} - {self.payment}"
    
