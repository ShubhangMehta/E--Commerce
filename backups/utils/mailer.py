# mailer.py
from django.core.mail import send_mail
from django.conf import settings


def send_backup_status_email(
    to_email,
    tenant_name,
    schema,
    backup_type,      # "daily" or "weekly"
    status,           # "success" or "failed"
    file_path=None,
    error_message=None,
):
    backup_type_label = backup_type.capitalize()
    status_label = status.upper()

    subject = f"[{backup_type_label} Backup {status_label}] {tenant_name}"

    if status == "success":
        message = f"""
Hello {tenant_name},

✅ Your {backup_type_label} backup has completed successfully.

Backup Details:
• Tenant Schema : {schema}
• Backup Type   : {backup_type_label}
• Storage Path  : {file_path}

No action is required from your side.

Regards,
E-Commerce Backup System
"""
    else:
        message = f"""
Hello {tenant_name},

❌ Your {backup_type_label} backup has FAILED.

Backup Details:
• Tenant Schema : {schema}
• Backup Type   : {backup_type_label}

Error Details:
{error_message or "Unknown error occurred during backup."}

Our team has been notified and will investigate.

Regards,
E-Commerce Backup System
"""

    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )