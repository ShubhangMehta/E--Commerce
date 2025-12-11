from backups.models import Backup, BackupAlert
from django.utils import timezone
from django.core.mail import send_mail
import datetime

def notify_backup_failure(tenant_schema, backup_date, error_message):
    """
    Create a failed backup entry, generate a backup alert, 
    and send an email notification.
    
    Args:
        tenant_schema (str): Name of the tenant.
        backup_date (str or datetime.datetime): Backup date as string "YYYY-MM-DD" or datetime object.
        error_message (str): Error message to log.
    
    Returns:
        BackupAlert instance
    """

    # If backup_date is a string, convert to datetime
    if isinstance(backup_date, str):
        backup_date = datetime.datetime.strptime(backup_date, "%Y-%m-%d")

    # Make it timezone-aware if naive
    if timezone.is_naive(backup_date):
        backup_date = timezone.make_aware(backup_date, timezone.get_current_timezone())

    # 1) Create failed Backup entry
    backup = Backup.objects.create(
        type="tenant",
        tenant_schema=tenant_schema,
        status="failed",
        started_at=backup_date,
        finished_at=timezone.now(),
        error_message=error_message,
    )

    # 2) Create alert linked to backup
    alert = BackupAlert.objects.create(
        backup=backup,
        retention_weeks=4,
    )

    # 3) Send email notification
    send_mail(
        subject=f"Backup Restore Failed: {tenant_schema}",
        message=(
            f"Backup restore failed for tenant: {tenant_schema}\n"
            f"Date: {backup_date}\n\n"
            f"Error:\n{error_message}"
        ),
        from_email="admin@example.com",
        recipient_list=["your_email@example.com"],
        fail_silently=True,
    )

    return alert
