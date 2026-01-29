from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class CustomerUser(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=128)  # store hashed password
    is_active = models.BooleanField(default=True)

    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Verify a password against the stored hash"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.email

class ShippingAddress(models.Model):
    ADDRESS_TYPES = (
        ("home", "Home"),
        ("work", "Work"),
        ("office", "Office"),
        ("other", "Other"),
    )

    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE)
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
