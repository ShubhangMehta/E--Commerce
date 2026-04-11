# from django.db import models
# from django.contrib.auth.models import User

# class Order(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('paid', 'Paid'),
#         ('shipped', 'Shipped'),
#         ('delivered', 'Delivered'),
#         ('cancelled', 'Cancelled'),
#     ]

#     client = models.ForeignKey(User, on_delete=models.CASCADE)
#     order_number = models.CharField(max_length=50, unique=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.order_number

# class Order(models.Model):
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=50, default='Pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order {self.order_number} - {self.customer_name}"
    




from django.db import models
from users.models import SubjectMember
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    # tenant/store
    tenant = models.CharField(max_length=100)

    # customer (storefront identity)
    subject = models.ForeignKey(
        SubjectMember,
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,   # allow NULL for existing rows
        blank=True
    )

    # totals
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
    shipping_house_no= models.CharField(max_length=20, default="Not Provided")
    shipping_landmark= models.CharField(max_length=20, default="Not Provided")
    shipping_address = models.TextField(default="Not Provided")
    shipping_city = models.CharField(max_length=100,default="Not Provided")
    shipping_state = models.CharField(max_length=100,default="Not Provided")
    shipping_postal_code = models.CharField(max_length=20,default="Not Provided")

    created_at = models.DateTimeField(auto_now_add=True)

   # def save(self, *args, **kwargs):
   #     if not self.order_number:
   #         self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
   #     super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )

    # ⭐ GENERIC PRODUCT RELATION (supports SingleProduct OR MultiProduct)
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # object_id = models.PositiveIntegerField()
    # product = GenericForeignKey("content_type", "object_id")

    # 🔒 SNAPSHOT (SUPER IMPORTANT — never remove)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order #{self.id}"

