import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone

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
        ]

    def __str__(self):
        return f"global_user_id={self.global_user_id} ({self.role})"

def invite_default_expiry():
    return timezone.now() + timedelta(days=7)

class StaffInvite(models.Model):
    email = models.EmailField(db_index=True)
    role = models.CharField(max_length=20, choices=TenantRole.choices, default=TenantRole.STAFF)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by_global_user_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=invite_default_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.revoked_at is None and self.accepted_at is None and self.expires_at > timezone.now()
    
    class Meta:
        indexes = [ models.Index(fields=["token"]), models.Index(fields=["email"]) ]


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
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default="home")
    is_default = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.address_line1}, {self.address_line2}, {self.landmark} {self.city}, {self.country}, {self.postal_code}"
    
    @property
    def formatted_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.landmark,
            self.city,
            self.state,
            self.country,
            self.postal_code,
        ]
        return ", ".join([p.strip() for p in parts if p and p.strip()])
        