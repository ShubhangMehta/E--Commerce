# from django.db import models
# from customers.models import Client as Client

# class TenantBackup(models.Model):
#     client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="backups")
#     schema_name = models.CharField(max_length=63)
#     backup_type = models.CharField(max_length=20, choices=[
#         ("db", "Database"),
#         ("media", "Media"),
#         ("full", "Full"),
#     ])
#     file_path = models.CharField(max_length=500)
#     file_size = models.BigIntegerField(null=True, blank=True)
#     checksum = models.CharField(max_length=128, blank=True, default="")
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_verified = models.BooleanField(default=False)


# class TenantRestoreRequest(models.Model):
#     STATUS_PENDING = "pending"
#     STATUS_APPROVED = "approved"
#     STATUS_REJECTED = "rejected"
#     STATUS_COMPLETED = "completed"

#     STATUS_CHOICES = [
#         (STATUS_PENDING, "Pending"),
#         (STATUS_APPROVED, "Approved"),
#         (STATUS_REJECTED, "Rejected"),
#         (STATUS_COMPLETED, "Completed"),
#     ]

#     client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="restore_requests")
#     requested_by_email = models.EmailField()
#     note = models.TextField(blank=True, default="")
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
#     requested_at = models.DateTimeField(auto_now_add=True)
#     processed_at = models.DateTimeField(null=True, blank=True)
    