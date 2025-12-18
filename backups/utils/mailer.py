from django.core.mail import send_mail
from django.conf import settings

def send_backup_status_email(
    to_email,
    tenant_name,
    schema,
    backup_type,
    status,
    file_path=None,
    error_message=None,
):
    subject = f"[Backup {status.upper()}] {tenant_name} - {backup_type}"

    if status == "success":
        message = ff"""
Backup Completed Successfully

Hello {tenant_name},

We are pleased to inform you that your {backup_type} backup has been completed successfully.

Backup Details:
• Schema: {schema}
• Storage Location: {file_path}
• Backup Type: {backup_type.capitalize()}

No action is required at this time.

If you have any questions or require assistance, please feel free to contact our support team.

Best regards,
E-Commerce Backup System
"""
    else:
        message = ff"""
Backup Failure Notification

Hello {tenant_name},

We regret to inform you that your {backup_type} backup has failed.

Backup Details:
• Schema: {schema}
• Backup Type: {backup_type.capitalize()}

Error Information:
{error_message}

Our system will continue to monitor this issue. If the problem persists or requires immediate attention, please contact our support team.

Regards,
E-Commerce Backup System
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False,
    )