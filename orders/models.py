from django.db import models
from users.models import SubjectMember
from catalog.models import SingleProduct
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class Coupon(models.Model):

    code = models.CharField(max_length=50, unique=True)

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    active = models.BooleanField(default=True)

    usage_limit = models.IntegerField(
        null=True,
        blank=True
    )

    used_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self, cart_total):
        now = timezone.now()

        if not self.active:
            return False

        if self.valid_from > now or self.valid_to < now:
            return False

        if cart_total < self.min_order_value:
            return False

        if self.usage_limit and self.used_count >= self.usage_limit:
            return False

        return True

    def __str__(self):
        return self.code
    
class Order(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    tenant = models.CharField(max_length=100, default="default_tenant")  # 🔥 TENANT FIELD (important for multi-tenancy)
    customer_email = models.EmailField(default="")
    customer_name = models.CharField(max_length=255, blank=True, default="")

    # customer (storefront identity)
    subject = models.ForeignKey(
        SubjectMember,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,   # allow NULL for existing rows
        blank=True
    )

    # totals
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(
            Coupon,
            on_delete=models.SET_NULL,
            null=True,
            blank=True
        )
        
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # order lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")

    # 🔥 shipping snapshot (VERY IMPORTANT)
    shipping_full_name = models.CharField(max_length=255, default="Not Provided")
    shipping_phone = models.CharField(max_length=20, default="Not Provided")
    shipping_house_no= models.CharField(max_length=100, default="Not Provided")
    shipping_landmark= models.CharField(max_length=100, default="Not Provided")
    shipping_address = models.TextField(default="Not Provided")
    shipping_city = models.CharField(max_length=100,default="Not Provided")
    shipping_state = models.CharField(max_length=100,default="Not Provided")
    shipping_postal_code = models.CharField(max_length=20,default="Not Provided")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #def save(self, *args, **kwargs):
    #    if not self.order_number:
    #        self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    #    super().save(*args, **kwargs)

    def __str__(self):
      return f"Order #{self.id}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )

    # ⭐ GENERIC PRODUCT RELATION (supports SingleProduct OR MultiProduct)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey("content_type", "object_id")

    # 🔒 SNAPSHOT (SUPER IMPORTANT — never remove)
    product_name_snapshot = models.CharField(max_length=255, default="")
    product_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    product_image_url_snapshot = models.URLField(blank=True, default="")    

    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name_snapshot} x {self.quantity}"
