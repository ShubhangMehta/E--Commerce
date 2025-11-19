from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.utils import timezone

# Create your models here.

class Client(TenantMixin):
    # Tenant Info 
    tenant_name = models.CharField(max_length=100)
    server_name = models.CharField(max_length=150, help_text="VPS or server identifier")
    desired_domain = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Tenant's desired subdomain (e.g., 'store1', 'bigco')."
    )
    created_on = models.DateField(auto_now_add=True)
    email=models.EmailField(null=True,blank=True)
    company=models.CharField(max_length=200,null=True,blank=True)
    address=models.TextField(null=True,blank=True)
    logo=models.ImageField(upload_to='tenant_logos/', null=True, blank=True)

    #  Subscription 
    PLAN_TYPE_CHOICES=[
        ('Basic','Basic'),
        ('Standard','Standard'),
        ('Premium','Premium')
    ]
    plan_type = models.CharField(max_length=50,choices=PLAN_TYPE_CHOICES,default='Basic')
    subscription_start = models.DateField(auto_now_add=True)
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

    # Payments
    total_orders_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_payment_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)

    PAYMENT_MODES = [
        ('COD', 'Cash on Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
    ]
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default='COD')
    PAYMENT_STATUS_CHOICES=[
        ('Unpaid','Unpaid'),
        ('Paid','Paid')
    ]
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES,default="Unpaid")
    PAYMENT_PLAN=[
        ('Weekly','Weekly'),
        ('Monthly','Monthly')
    ]
    payment_plan=models.CharField(max_length=20,choices=PAYMENT_PLAN,default='Weekly')

    #  Django Tenants Required
    auto_create_schema = True

    def __str__(self):
        return self.tenant_name
    
class Domain(DomainMixin):
    pass

class TenantRequest(models.Model):
    tenant_name = models.CharField(max_length=100)
    desired_domain = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    company = models.CharField(max_length=200,null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    PLAN_TYPE_CHOICES = [
        ('Basic', 'Basic'),
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
    ]
    plan_type = models.CharField(max_length=50,choices=PLAN_TYPE_CHOICES,default='Basic')
    PAYMENT_MODE_CHOICES = [
        ('COD', 'Cash On Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
    ]
    payment_mode = models.CharField(max_length=10,choices=PAYMENT_MODE_CHOICES,default='COD')
    PAYMENT_PLAN_CHOICES = [
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
            ]
    payment_plan=models.CharField(max_length=10,choices=PAYMENT_PLAN_CHOICES,default='Monthly')
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

