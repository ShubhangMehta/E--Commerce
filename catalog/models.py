from django.db import models


class SingleProduct(models.Model):
    brand_name = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    availability = models.BooleanField(default=True)

    seller = models.CharField(max_length=150)
    estimated_delivery = models.CharField(max_length=100)

    refundable = models.BooleanField(default=False)
    returnable = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    featured_order = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Position in homepage banner (1–3)"
        )


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SingleProductImage(models.Model):

    IMAGE_TYPE_CHOICES = (
        ("product", "Product Image"),
        ("banner", "Banner Image"),
    )

    product = models.ForeignKey(
        SingleProduct,
        related_name="images",
        on_delete=models.CASCADE
    )

    image = models.ImageField(upload_to="products/")

    
    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPE_CHOICES,
        default="product"
    )

    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "created_at"]

    def __str__(self):
        return f"{self.image_type} image for {self.product.name}"
