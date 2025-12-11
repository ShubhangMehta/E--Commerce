from django.core.management.base import BaseCommand
from backups.models import Backup, BackupAlert
from django.utils import timezone
from django.core.mail import send_mail

class Command(BaseCommand):
    help = "Simulate a backup failure and create alert"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Creating test failed backup..."))

        # Create fake failed backup
        backup = Backup.objects.create(
            type="tenant",
            tenant_schema="test_tenant",
            status="failed",
            started_at=timezone.now(),
            finished_at=timezone.now(),
            error_message="Simulated backup failure for testing."
        )

        # Create backup alert
        alert = BackupAlert.objects.create(
            backup=backup,
            retention_weeks=4
        )

        # Send test email
        send_mail(
            subject="⚠️ Backup Failure Detected",
            message=f"Backup for tenant '{backup.tenant_schema}' failed.\nError: {backup.error_message}",
            from_email="admin@example.com",
            recipient_list=["your_email@example.com"],
            fail_silently=False,
        )

        self.stdout.write(self.style.SUCCESS(f"Backup failure simulated. BackupAlert ID: {alert.id}"))