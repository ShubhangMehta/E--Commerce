from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
<<<<<<< HEAD

# Create your models here.
=======
from django.conf import settings


<<<<<<< HEAD
# ================================================================
#   SHARED CUSTOMER MODEL (USED BY ALL USERS)
# ================================================================
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
=======
>>>>>>> 69fec36 (Razorpay Integration)

'''
class Customer(models.Model): #my
    """
    Represents an end-user customer using the platform.
    """

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)       # Unique login/contact email
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    joined_date = models.DateTimeField(auto_now_add=True)  # Date customer registered

    def __str__(self):
        return self.name

    class Meta:
        app_label = "customers"
        # important for django-tenants
        managed = True
        #tenant_schema = True   # <<— this makes it a TENANT MODEL
'''



class SubscriptionPlan(models.Model): #same
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


<<<<<<< HEAD
# ================================================================
#   USER SUBSCRIPTIONS (INDIVIDUAL ACCOUNT PLANS)
# ================================================================

class UserSubscription(models.Model):
    """
    Maps a platform user to a subscription plan.
    Tracks subscription duration and status.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")

    def save(self, *args, **kwargs):
        # Automatically calculate end date
        if self.plan and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'} ({self.get_status_display()})"


# ================================================================
#   USER PAYMENTS
# ================================================================

class UserPayment(models.Model):
    """
    Stores payment transactions made by individual users.
    """

    PAYMENT_METHODS = [
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("upi", "UPI"),
        ("net_banking", "Net Banking"),
        ("wallet", "Wallet"),
    ]

    PAYMENT_STATUS = [
        ("paid", "Paid"),
        ("unpaid", "Unpaid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_PLAN = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_plan = models.CharField(max_length=20, choices=PAYMENT_PLAN, default="monthly")

    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="unpaid")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.method} - {self.get_status_display()}"


# ================================================================
#   USER INVOICES
# ================================================================

class UserInvoice(models.Model):
    """
    Stores invoices generated for user subscription payments.
    """

    INVOICE_TYPE = [
        ("manual", "Manually Generated"),
        ("auto", "Auto Generated"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE)
    payment = models.OneToOneField(UserPayment, on_delete=models.CASCADE)

    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE, default="auto")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_invoice_type_display()})"


# ================================================================
#   USER REFUND REQUESTS
# ================================================================

class UserRefundRequest(models.Model):
    """
    Refund / cancellation request submitted by users.
    """

    REFUND_TYPES = [
        ("product_issue", "Product/Service Issue"),
        ("late_delivery", "Late Delivery"),
        ("payment_error", "Payment Error"),
        ("duplicate_payment", "Duplicate Payment"),
        ("subscription_cancel", "Subscription Cancellation"),
        ("others", "Others"),
    ]

    REFUND_POLICIES = [
        ("full", "Full Refund"),
        ("partial", "Partial Refund"),
        ("no_refund", "No Refund"),
    ]

    REFUND_STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment = models.ForeignKey(UserPayment, on_delete=models.CASCADE)

    refund_type = models.CharField(max_length=50, choices=REFUND_TYPES)
    refund_policy = models.CharField(max_length=50, choices=REFUND_POLICIES, default="partial")
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default="pending")

    reason = models.TextField()
    terms_and_conditions = models.TextField(
        default="Refund requests must comply with the platform’s current policy."
    )

    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    approved_by = models.CharField(max_length=100, blank=True, null=True)
    is_refunded = models.BooleanField(default=False)

    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    policy_version = models.CharField(max_length=10, default="v1.0")

    def __str__(self):
        return f"Refund by {self.user.username} - {self.get_status_display()}"


# ================================================================
#   MULTI-TENANT CLIENT MODELS
# ================================================================

class Client(TenantMixin):
<<<<<<< HEAD
    name = models.CharField(max_length=100)
    paid_until = models.DateField()
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
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
        unique_together = ('plan', 'billing_cycle')

    def __str__(self):
        return f"{self.plan} - {self.get_billing_cycle_display()}"
    
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
        if self.is_trial and self.has_successful_payment:
            raise ValidationError("Trail subscriptions must not have payment")
        
        #Paid plans must have payment before activations
        if not self.is_trial and self.pricing and not self.has_successful_payment and self.status == 'active':
            raise ValidationError("Paid subscription require payments to be active")
        
    class Meta:
        ordering = ['-end_date']  # Latest subscription first

    def save(self, *args, **kwargs):

        now = timezone.now()
        is_new = self.pk is None

        #First Save - ensure PK exists
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
                
                self.status = 'expired' if self.end_date < now else 'active'

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
        plan_name = self.plan.get_name_display() if self.plan else 'No Plan'
        return f"{self.client.tenant_name} - {plan_name} ({self.status})"
    

class TenantRequest(models.Model):
    """
    Stores sign-up requests from businesses wanting to create a tenant.
    """
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, null=True, blank=True)
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
    #is_approved = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['desired_domain'], 
                condition=Q(status__in=['pending_payment', 'trial_created', 'paid_created']),
                name='uniq_reserved_domain_active_requests', 
                )
        ]

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
#  Invoice Model
# ---------------------------------------------
class Invoice(models.Model):
    INVOICE_TYPE = [
        ('manual', 'Manually Generated'),
        ('auto', 'Auto Generated'),
    ]

    STATUS_CHOICES = [
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    tenant_request = models.ForeignKey(TenantRequest, on_delete=models.CASCADE, related_name='invoices')

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(ClientSubscription, on_delete=models.SET_NULL, null=True, blank=True)

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

 
=======
    """
    A tenant (client) in the multi-tenant architecture.
    Each client gets its own database schema.
    """
=======
>>>>>>> 69fec36 (Razorpay Integration)

class Client(TenantMixin): #humera
    tenant_name = models.CharField(max_length=100)
    server_name = models.CharField(max_length=150, help_text="VPS or server identifier")
    desired_domain = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    # Usage & Analytics
    storage_used_mb = models.FloatField(default=0.0)
    product_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    visitor_count_7d = models.IntegerField(default=0)
    visitor_count_30d = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)

    auto_create_schema = True

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
    ]

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




class Domain(DomainMixin): #same
    """
    Domain mapping for tenant.
    """
    pass
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)



class TenantRequest(models.Model): #same
    """
    Stores sign-up requests from businesses wanting to create a tenant.
    """

    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)

    email = models.EmailField(blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="tenant_logos/", blank=True, null=True)

    # Subscription plan chosen at signup
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)

    PAYMENT_METHODS = [
        ("COD", "Cash On Delivery"),
        ("UPI", "UPI"),
        ("CARD", "Credit/Debit Card"),
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_METHODS, default="COD")

    PAYMENT_PLANS = [
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
    ]
    payment_plan = models.CharField(max_length=10, choices=PAYMENT_PLANS, default="Monthly")

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




class Ticket(models.Model): #humera
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



class ClientPayment(models.Model): #my
    """
    Stores payments made by tenants (business clients).
    """

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    method = models.CharField(max_length=20, choices=TenantRequest.PAYMENT_METHODS)
    payment_plan = models.CharField(max_length=20, choices=TenantRequest.PAYMENT_PLANS)

    transaction_id = models.CharField(max_length=100, unique=True)

    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("unpaid", "Unpaid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unpaid")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.tenant_name} - {self.method} - {self.status}"




class ClientSubscription(models.Model): #my
    """
    Tracks subscription plan and lifecycle for each tenant client.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
        ("cancelled", "Cancelled"),
        ("pending", "Pending"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)

    duration_days = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    payment = models.ForeignKey(
        ClientPayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
    )

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    grace_period_days = models.PositiveIntegerField(default=3)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="active")
    auto_renew = models.BooleanField(default=False)

    manual_override = models.BooleanField(
        default=False,
        help_text="Allow admin to manually override date or status"
    )

    # Reference to payment transaction for this subscription
    payment_reference = models.ForeignKey(
        ClientPayment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_references",
    )

    def save(self, *args, **kwargs):
        """
        Handles:
            - auto-assigning start/end dates
            - updating client status
            - syncing storage limits
        """
        if not self.manual_override:

            # Set default start date
            if not self.start_date:
                self.start_date = timezone.now()

            # Auto-select end date if missing
            if self.plan and not self.end_date:
                self.end_date = self.start_date + timedelta(days=self.plan.duration_days)

            # Update subscription status
            now = timezone.now()
            if self.end_date and self.end_date < now:
                self.status = "expired"
            elif self.status not in ["suspended", "cancelled"]:
                self.status = "active"

            # Update client status
            self.client.status = "Active" if self.status == "active" else "Suspended"

            # Sync storage capacity based on plan
            if self.plan:
                self.client.storage_used_mb = self.plan.storage_limit_mb

            self.client.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.tenant_name} - {self.plan.name if self.plan else 'No Plan'} ({self.status})"



class ClientInvoice(models.Model): #my
    """
    Invoice generated for tenant billing.
    """

    INVOICE_TYPE = [
        ("manual", "Manually Generated"),
        ("auto", "Auto Generated"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    subscription = models.ForeignKey(ClientSubscription, on_delete=models.CASCADE)
    payment = models.OneToOneField(ClientPayment, on_delete=models.CASCADE)

    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE, default="auto")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.get_invoice_type_display()})"




class ClientRefundRequest(models.Model): #same
    """
    Refund request issued by a tenant.
    """

    REFUND_TYPES = [
        ("product_issue", "Product/Service Issue"),
        ("late_delivery", "Late Delivery"),
        ("payment_error", "Payment Error"),
        ("duplicate_payment", "Duplicate Payment"),
        ("subscription_cancel", "Subscription Cancellation"),
        ("others", "Others"),
    ]

    REFUND_POLICIES = [
        ("full", "Full Refund"),
        ("partial", "Partial Refund"),
        ("no_refund", "No Refund"),
    ]

    REFUND_STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    payment = models.ForeignKey(ClientPayment, on_delete=models.CASCADE)

    refund_type = models.CharField(max_length=50, choices=REFUND_TYPES)
    refund_policy = models.CharField(max_length=50, choices=REFUND_POLICIES, default="partial")
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default="pending")

    reason = models.TextField()
    terms_and_conditions = models.TextField(
        default="Refund requests must comply with the platform’s current policy and can be rejected if criteria are not met."
    )

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

PLAN_CHOICES = (
    ("Basic", "Basic"),
    ("Standard", "Standard"),
    ("Premium", "Premium"),
)

BILLING_INTERVALS = (
    ("monthly", "Monthly"),
    ("yearly", "Yearly"),
)


class RzpPlan(models.Model):
    """
    Razorpay plan created for automated billing.
    """

    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    interval = models.CharField(max_length=20, choices=BILLING_INTERVALS, default="monthly")

    amount_in_paise = models.PositiveIntegerField(
        help_text="100.00 INR → 10000 paise"
    )

    razorpay_plan_id = models.CharField(
        max_length=64, blank=True, null=True, help_text="Maps to an existing RZP plan if needed"
    )

    features = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"


class RzpSubscription(models.Model):
    """
    Razorpay subscription record for automated billing.
    """

    client = models.ForeignKey(
        "customers.Client", on_delete=models.SET_NULL, blank=True, null=True
    )

    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)     # subdomain
    email = models.EmailField()

    plan = models.ForeignKey(RzpPlan, on_delete=models.PROTECT)
    interval = models.CharField(max_length=20, choices=BILLING_INTERVALS, default="monthly")

    status = models.CharField(
        max_length=20,
        choices=[
            ("created", "Created"),
            ("active", "Active"),
            ("pending", "Pending"),
            ("past_due", "Past Due"),
            ("cancelled", "Cancelled"),
            ("expired", "Expired"),
        ],
        default="created"
    )

    razorpay_subscription_id = models.CharField(max_length=64, unique=True, blank=True, null=True)

    started_at = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.plan.name} ({self.status})"




class RzpInvoice(models.Model):
    """
    Razorpay invoice created for subscription billing.
    """

    subscription = models.ForeignKey(RzpSubscription, on_delete=models.CASCADE, related_name="invoices")

    invoice_number = models.CharField(max_length=50, unique=True)
    amount_in_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="INR")

    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("paid", "Paid"), ("refunded", "Refunded")],
        default="pending"
    )

    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.invoice_number


class RzpPayment(models.Model):
    """
    Razorpay payment for a subscription invoice.
    """

    subscription = models.ForeignKey(RzpSubscription, on_delete=models.CASCADE, related_name="payments")
    invoice = models.ForeignKey(RzpInvoice, on_delete=models.SET_NULL, blank=True, null=True)

    razorpay_payment_id = models.CharField(max_length=64, unique=True)
    amount_in_paise = models.PositiveIntegerField()
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
    