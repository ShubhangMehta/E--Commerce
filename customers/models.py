from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ValidationError

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
        ('trial', 'Trial'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    BILLING_CHOICES = [
        ('trial', 'Free Trial'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    storage_limit_mb = models.PositiveIntegerField(default=500)  # Feature: storage per plan
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.get_name_display()
    
class PlanPricing(models.Model):
    BILLING_CHOICES = [
        ('trial', 'Trial'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=0)
    #is_trial = models.BooleanField(default=False)

    class Meta:
        unique_together = ('name', 'billing_cycle')

    @property
    def is_trial(self):
        return self.price == 0

    def __str__(self):
        return f"{self.plan} - {self.get_billing_cycle_display()}"
    
    # def clean(self):
    #     if self.billing_cycle == 'trial' and not self.plan.is_trial:
    #         raise ValidationError("Only trial plans can have trial billing cycle")
# ---------------------------------------------
#  Payment Details
# ---------------------------------------------
# class Payment(models.Model):
#     client = models.ForeignKey(Client, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=8, decimal_places=2)
    
#     PAYMENT_PLANS = [
#         ('Monthly', 'Monthly'), #499 999 1999
#         ('Yearly', 'Yearly'), 
#     ]
#     payment_plan = models.CharField(max_length=10, choices=PAYMENT_PLANS, default='Monthly')
#     #payment_plan = models.CharField(max_length=20, choices=TenantRequest.PAYMENT_PLANS)

#     transaction_id = models.CharField(max_length=100, unique=True)
#     status_choices = [
#         ('paid', 'Paid'),
#         ('unpaid', 'Unpaid'),
#         ('failed', 'Failed'),
#         ('refunded', 'Refunded'),
#     ]
#     status = models.CharField(max_length=20, choices=status_choices, default='unpaid')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.client.tenant_name} - {self.payment_plan} - {self.status}"

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

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    pricing = models.ForeignKey(PlanPricing,on_delete=models.PROTECT,null=True,blank=True)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    
    manual_override = models.BooleanField(
        default=False,
        help_text="If enabled, admin can manually modify subscription dates or status."
    )

    @property
    def is_trial(self):
        return self.pricing and self.pricing.billing_cycle == 'trial'
    
    @property
    def has_successful_payment(self):
        if not self.pk:
            return False
        return self.payments.filter(status='captured').exists()
    
    def activate_from_payment(self):
        """
        Called Only after RazorPay confirms payment captured.
        """
        if not self.pricing or self.is_trial:
            return
        
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=self.pricing.duration_days)
        self.status = 'active'
        self.save(update_fields=['start_date', 'end_date', 'status'])

    def clean(self):
        #trial will never have payment
        if self.is_trial and self.payment:
            raise ValidationError("Trail subscriptions must not have payment")
        
        #Paid plans must have payment before activations
        if not self.is_trial and self.pricing and not self.payment and self.status == 'active':
            raise ValidationError("Paid subscription require payments to be active")
        
    class Meta:
        ordering = ['-end_date']  # Latest subscription first

    def save(self, *args, **kwargs):

        now = timezone.now()
        is_new = self.pk is None

        if is_new:
            super().save(*args, **kwargs)
            return

        if not self.manual_override:
            # Set subscription start and end dates if not provided
            if not self.start_date:
                self.start_date = now()

            #-------------
            #Trial Logic (subscription)
            #-------------
            if self.is_trial:
                #Enforce trial duration (7 days)
                if not self.end_date:
                    self.end_date = self.start_date + timedelta(days=7)

            #-------------
            #Paid Logic (subscription)
            #-------------
            else:
                #Paid plan must come via explicit upgrade
                if not self.has_successful_payment:
                    self.status = 'expired'
                else:
                    if not self.end_date:
                        self.end_date = self.start_date + timedelta(days=self.pricing.duration_days)
                    self.status = 'expired' if self.end_date < now else 'active'

        super().save(*args, **kwargs)

    def __str__(self):
        plan_name = self.plan.name if self.plan else 'No Plan'
        return f"{self.client.tenant_name} - {plan_name} ({self.status})"
    

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
    pricing = models.ForeignKey(PlanPricing, on_delete=models.PROTECT,null=True,blank=True)

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

# ================================================================
#   RAZORPAY BILLING MODELS
# ================================================================

class RzpPayment(models.Model):
    """
    Razorpay payment for a subscription invoice.
    """
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    EVENT_CHOICES = [
        ('payment.created', 'Payment Created'),
        ('payment.authorized', 'Payment Authorized'),
        ('payment.captured', 'Payment Captured'),
        ('payment.failed', 'Payment Failed'),
        ('refund.processed', 'Refund Processed'),
    ]

    subscription = models.ForeignKey(ClientSubscription, on_delete=models.CASCADE, related_name="payments")
    #invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True)

    razorpay_payment_id = models.CharField(max_length=64, blank=True, null=True)
    amount= models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    event = models.CharField(max_length=50, choices=EVENT_CHOICES, blank=True)

    captured = models.BooleanField(default=False)
    failure_reason=models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.razorpay_payment_id or f"RZP Attempt {self.id}"


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
    payment = models.OneToOneField(RzpPayment, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE, default='auto')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_invoice_type_display()})"

