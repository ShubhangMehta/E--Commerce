from django.db import models
from django.core.exceptions import ValidationError

class Category(models.Model):

    name = models.CharField(max_length=150)
    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class SubCategory(models.Model):

    category = models.ForeignKey(
        Category,
        related_name="subcategories",
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=150)
    class Meta:
        unique_together = ("category", "name")#prevents creating duplicate subcategories


    def __str__(self):
        return f"{self.category.name} - {self.name}"

class SingleProduct(models.Model):
    brand_name = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
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
    def clean(self):
        if self.sub_category and self.sub_category.category != self.category:
         raise ValidationError(
                "Subcategory does not belong to the selected category."
            )
    def save(self, *args, **kwargs):
        self.full_clean() #the clean() does not run automatically when save is called it only runs in model forms and django admin so if a product is created from terminal this clean function will also run automatically 
        super().save(*args, **kwargs)



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
