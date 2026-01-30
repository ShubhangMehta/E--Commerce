from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings

def send_backup_failure_alert(backup, error_message):
    """
    Sends email alerts to superusers when a backup fails.
    """

    User = get_user_model()
    superusers = User.objects.filter(is_superuser=True).values_list('email', flat=True)

    subject = f"[BACKUP FAILURE] Backup ID {backup.id} ({backup.type})"
    body = f"""
Backup Failed!

Backup ID: {backup.id}
Type: {backup.type}
Tenant: {backup.tenant_schema or 'GLOBAL'}
Created At: {backup.created_at}

Error:
{error_message}

Please check the admin panel for more details.
    """

    # Send email only if superusers have emails
    if superusers:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            list(superusers),
            fail_silently=True,
        )