from django.db import models
from django.contrib.auth.models import User
from customers.models import Client

class TenantRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Staff"
    CUSTOMER = "CUSTOMER", "Customer"



class SubjectMember(models.Model):
    """
    Tenant-scoped "who is this global user inside this tenant?"
    Stored in tenant schema.

    """
    global_user_id = models.BigIntegerField(db_index=True)
    role = models.CharField(max_length=20, choices=TenantRole.choices)
    full_name = models.CharField(max_length=255)
    email=models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["global_user_id", "role"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["global_user_id"], name="uniq_tenant_member_global_user"),
            models.UniqueConstraint(fields=["email"], name="uniq_subjectmember_email"),
        ]

    def __str__(self):
        return f"global_user_id={self.global_user_id} ({self.role})"


class Coordinate(models.Model):
    ADDRESS_TYPES = (
        ("home", "Home"),
        ("work", "Work"),
        ("office", "Office"),
        ("other", "Other"),
    )

    user = models.ForeignKey(
        SubjectMember,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    house_no = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default="home")
    is_default = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.house_no}, {self.landmark} {self.city}, {self.postal_code}"
    
