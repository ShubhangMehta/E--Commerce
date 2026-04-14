from django.db import models
from customers.models import Client as Client

class TenantBackup(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="backups")
    schema_name = models.CharField(max_length=63)
    backup_type = models.CharField(max_length=20, choices=[
        ("db", "Database"),
        ("media", "Media"),
        ("full", "Full"),
    ])
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

