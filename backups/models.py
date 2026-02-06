from django.db import models
from django.conf import settings


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

    def __str__(self):
        if self.type == self.GLOBAL:
            return f"Global Backup {self.created_at:%Y-%m-%d %H:%M}"
        return f"{self.tenant_schema} Backup {self.created_at:%Y-%m-%d %H:%M}"


from django.db import models
from django.conf import settings



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
        verbose_name = "Backup Log"
        verbose_name_plural = "Backup Logs"

    def __str__(self):
        return f"[{self.level}] {self.timestamp:%Y-%m-%d %H:%M:%S}"



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
        verbose_name = "Global Backup Metadata"
        verbose_name_plural = "Global Backups"

    def __str__(self):
        return f"GlobalBackup (Retention: {self.retention_weeks} weeks)"