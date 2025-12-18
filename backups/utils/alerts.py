from django.core.mail import send_mail
from django.conf import settings
from backups.models import Backup, BackupAlert
from django.utils import timezone


def notify_backup_failure(backup: Backup):
    """
    Creates a BackupAlert and sends email notification.
    """

    alert = BackupAlert.objects.create(
        backup=backup,
        retention_weeks=4
    )

    subject = f"❌ Backup Failed [{backup.type.upper()}]"
    tenant = backup.tenant_schema or "GLOBAL"

    message = f"""
🚨 Backup Failure Alert

A scheduled backup operation has failed and requires attention.

Tenant Schema   : {tenant}
Backup Type     : {backup.type.upper()}
Start Time      : {backup.started_at}
End Time        : {backup.finished_at}

Failure Reason:
{backup.error_message}

Next Steps:
• Review the backup logs and error details
• Verify database connectivity and storage availability
• Re-run the backup job after resolving the issue

If this failure repeats, escalate to the infrastructure or database team.

— E-Commerce Platform | Backup Monitoring System
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    return alert