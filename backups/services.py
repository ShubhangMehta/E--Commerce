import os
from django.utils import timezone
from backups.models import Backup
from customers.models import Client
from backups.utils.mailer import send_backup_status_email
from django.core.mail import send_mail
from django.conf import settings
from .utils.alerts import notify_backup_failure
from supabase import create_client
import subprocess


supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

def generate_backup_for_tenant(client, backup_type):
    """
    client: customers.models.Client
    backup_type: daily | weekly | master
    """

    backup = Backup.objects.create(
        type=backup_type,
        tenant_schema=client.schema_name,  # from TenantMixin
        status="running",
        started_at=timezone.now(),
    )

    try:
        # ACTUAL BACKUP LOGIC
        run_backup_script(client, backup_type)

        backup.status = "success"
        backup.finished_at = timezone.now()
        backup.save()

        # ✅ SUCCESS EMAIL
        file_path = run_backup_script(client, backup_type)
        if client.email:
            send_backup_status_email(
            to_email=client.email,
            tenant_name=client.tenant_name,
            schema=client.schema_name,
            backup_type=backup_type,
            status="success",
            file_path=file_path,
            )

        return {"status": "success"}

    except Exception as e:
        backup.status = "failed"
        backup.finished_at = timezone.now()
        backup.error_message = str(e)
        backup.save()

        # ❌ DB ALERT
        notify_backup_failure(backup)

        # ❌ FAILURE EMAIL
        if client.email:
            send_backup_status_email(
                to_email=client.email,
                tenant_name=client.tenant_name,
                schema=client.schema_name,
                backup_type=backup_type,
                status="failed",
                error_message=str(e),
            )

        return {"status": "failed", "error": str(e)}



def upload_to_bucket(local_path, remote_path):
    with open(local_path, "rb") as f:
        supabase.storage.from_("backups").upload(remote_path, f)

#change run_backu-_scripts
def run_backup_script(client, backup_type):
    """
    Verifies that the backup created by shell script exists in Supabase.
    Raises Exception if not found.
    """
    date = timezone.now().date()
    file_path = f"tenants/{client.schema_name}/{backup_type}/{date}.dump"

    # Verify backup exists in bucket
    files = supabase.storage.from_("backups").list(
        f"tenants/{client.schema_name}/{backup_type}"
    )

    if not any(f["name"] == f"{date}.dump" for f in files):
        raise Exception("Backup file not found in storage")

    return file_path


def verify_backup_in_bucket(file_path):
    folder = file_path.rsplit("/", 1)[0]
    files = supabase.storage.from_("backups").list(folder)

    return any(f["name"] in file_path for f in files)