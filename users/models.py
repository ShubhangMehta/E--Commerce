from django.db import models
from django.contrib.auth.models import User

class CustomerUser(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile"
    )

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.email


class CustomerAddress(models.Model):
    ADDRESS_TYPES = (
        ("home", "Home"),
        ("work", "Work"),
        ("office", "Office"),
        ("other", "Other"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    house_no = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default="home")
    is_default = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.house_no}, {self.landmark} {self.city}, {self.postal_code}"
