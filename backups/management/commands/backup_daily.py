import os
import subprocess
import tempfile
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from django_tenants.utils import schema_context
from customers.models import Client

from backups.models import Backup, BackupLog
from backups.utils.upload_to_supabase import upload_daily_backup
from backups.utils.mailer import send_backup_status_email


class Command(BaseCommand):
    help = "Run daily tenant backups and send instant email notifications"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Starting DAILY tenant backups...")

        for tenant in Client.objects.all():
            with schema_context(tenant.schema_name):
                self.stdout.write(f"📦 Backing up tenant: {tenant.schema_name}")

                backup = Backup.objects.create(
                    type=Backup.TENANT,
                    tenant_schema=tenant.schema_name,
                    status="running",
                    started_at=timezone.now(),
                )

                try:
                    temp_dump = tempfile.NamedTemporaryFile(delete=False, suffix=".dump")

                    dump_cmd = [
                        "pg_dump",
                        "-Fc",
                        "-U", settings.DATABASES["default"]["USER"],
                        "-h", settings.DATABASES["default"]["HOST"],
                        "-p", str(settings.DATABASES["default"]["PORT"]),
                        "-d", settings.DATABASES["default"]["NAME"],
                        "-f", temp_dump.name,
                    ]

                    process = subprocess.run(
                        dump_cmd,
                        capture_output=True,
                        text=True,
                        env={"PGPASSWORD": settings.DATABASES["default"]["PASSWORD"]},
                    )

                    if process.returncode != 0:
                        raise Exception(process.stderr)

                    file_path = f"tenants/daily/{timezone.now().date()}/{tenant.schema_name}.dump"
                    upload_daily_backup(
                        tenant.schema_name,
                        str(timezone.now().date()),
                        temp_dump.name,
                    )

                    uploaded_path = file_path

                    backup.status = "success"
                    backup.file_path = uploaded_path
                    backup.file_size = os.path.getsize(temp_dump.name)
                    backup.finished_at = timezone.now()
                    backup.save()

                    BackupLog.objects.create(
                        backup=backup,
                        level=BackupLog.LEVEL_INFO,
                        message="Daily tenant backup completed successfully.",
                    )

                    # ✅ SUCCESS EMAIL — SENT INSTANTLY
                    if tenant.email:
                        send_backup_status_email(
                            to_email=tenant.email,
                            tenant_name=tenant.tenant_name,
                            schema=tenant.schema_name,
                            backup_type="daily",
                            status="success",
                            file_path=uploaded_path,
                        )

                except Exception as e:
                    backup.status = "failed"
                    backup.error_message = str(e)
                    backup.finished_at = timezone.now()
                    backup.save()

                    BackupLog.objects.create(
                        backup=backup,
                        level=BackupLog.LEVEL_ERROR,
                        message=str(e),
                    )

                    # ❌ FAILURE EMAIL — SENT INSTANTLY
                    send_backup_status_email(
                        to_email=tenant.email,
                        tenant_name=tenant.tenant_name,
                        schema=tenant.schema_name,
                        backup_type="daily",
                        status="failed",
                        error_message=str(e),
                    )

                    self.stderr.write(f"❌ Backup failed for {tenant.schema_name}")