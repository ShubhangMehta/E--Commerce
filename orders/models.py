from django.db import models
from users.models import SubjectMember
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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

    # order lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

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

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    product_image_url = models.URLField(blank=True, default="")

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
