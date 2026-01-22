from django.db import models
from django.conf import settings

from django.utils import timezone

########----
#Backup Models
########----
class Backup(models.Model):
    # per-tenant backup record (daily/weekly)
    TENANT = "tenant"
    GLOBAL = "global"
    TYPE_CHOICES = [(TENANT, "Tenant"), (GLOBAL, "Global")]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TENANT)
    tenant_schema = models.CharField(max_length=200, blank=True, null=True)  # null for global
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    file_path = models.CharField(max_length=1024, blank=True, null=True)   # supabase storage path
    file_size = models.BigIntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, default="pending")  # pending, running, success, failed
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "backup"

    def __str__(self):
        if self.type == self.GLOBAL:
            return f"Global Backup {self.created_at:%Y-%m-%d %H:%M}"
        return f"{self.tenant_schema} Backup {self.created_at:%Y-%m-%d %H:%M}"


    """def make_aware_safe(dt):
        return timezone.make_aware(dt) if timezone.is_naive(dt) else dt"""


from django.db import models
from django.conf import settings

########----
#Backup Log models
########----

class BackupLog(models.Model):
    LEVEL_INFO = "INFO"
    LEVEL_ERROR = "ERROR"

    LEVEL_CHOICES = [
        (LEVEL_INFO, "Info"),
        (LEVEL_ERROR, "Error"),
    ]

    backup = models.ForeignKey(
        "Backup",
        on_delete=models.CASCADE,
        related_name="logs",
        db_index=True,
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=LEVEL_INFO)
    message = models.TextField()

    class Meta:
        ordering = ["timestamp"]
        db_table = "backup_log"

        verbose_name = "Backup Log"
        verbose_name_plural = "Backup Logs"

    def __str__(self):
        return f"[{self.level}] {self.timestamp:%Y-%m-%d %H:%M:%S}"


########----
#Global Backup models
########----

class GlobalBackup(models.Model):
    backup = models.OneToOneField(
        "Backup",
        on_delete=models.CASCADE,
        related_name="global_meta",
    )
    retention_weeks = models.PositiveIntegerField(default=4)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "globalbackup_log"
        verbose_name = "Global Backup Metadata"
        verbose_name_plural = "Global Backups"

    def __str__(self):
        return f"GlobalBackup (Retention: {self.retention_weeks} weeks)"



########----
# Backup Alerts
########----

class BackupAlert(models.Model):
    backup = models.OneToOneField(
        "Backup",
        on_delete=models.CASCADE,
        related_name="alert",
    )

    retention_weeks = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        db_table = "backup_alert"
        verbose_name = "Backup Alert"
        verbose_name_plural = "Backup Alerts"

    def __str__(self):
        tenant = self.backup.tenant_schema or "GLOBAL"
        return f"Alert for {tenant} (Backup ID: {self.backup.id})"




# backups/models.py
from django.db import models

# backups/models.py
"""class BackupFailure(models.Model):
    tenant_name = models.CharField(max_length=255)
    backup_type = models.CharField(max_length=50)  # daily/weekly/master
    status = models.CharField(max_length=10)  # success/failed
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "backup_failure_log"  # custom table name
        ordering = ["-timestamp"]
        verbose_name = "Backup Failure"
        verbose_name_plural = "Backup Failures"

    def __str__(self):
        return f"{self.tenant_name} - {self.backup_type} - {self.status}"

        
        """