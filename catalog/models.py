from django.db import models

class SubCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class SingleProduct(models.Model):

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )
    brand_name = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()

    availability = models.BooleanField(default=True)

    seller = models.CharField(max_length=150)
    estimated_delivery = models.CharField(max_length=100)

    refundable = models.BooleanField(default=False)
    returnable = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SingleProductImage(models.Model):
    product = models.ForeignKey(
        SingleProduct,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"

# multi product models 
class MultiCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MultiSubCategory(models.Model):
    category = models.ForeignKey(
        MultiCategory,
        related_name="subcategories",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class MultiProduct(models.Model):
    category = models.ForeignKey(
        MultiCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products"
    )
    subcategory = models.ForeignKey(
        MultiSubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    brand_name = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    description = models.TextField()

    availability = models.BooleanField(default=True)

    seller = models.CharField(max_length=150)
    estimated_delivery = models.CharField(max_length=100)

    refundable = models.BooleanField(default=False)
    returnable = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class VariantType(models.Model):
    name = models.CharField(max_length=50)  # Color, Size

    def __str__(self):
        return self.name


class VariantValue(models.Model):
    variant_type = models.ForeignKey(
        VariantType,
        related_name="values",
        on_delete=models.CASCADE
    )
    value = models.CharField(max_length=50)  # Red, M, XL

    def __str__(self):
        return f"{self.variant_type.name}: {self.value}"

#price + stock per varient
class MultiProductVariant(models.Model):
    product = models.ForeignKey(
        MultiProduct,
        related_name="variants",
        on_delete=models.CASCADE
    )
    variant_value = models.ForeignKey(
        VariantValue,
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.variant_value}"


class MultiProductImage(models.Model):
    product = models.ForeignKey(
        MultiProduct,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="multi_products/")
    is_primary = models.BooleanField(default=False)
