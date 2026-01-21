import os
import subprocess
import tempfile

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from django_tenants.utils import schema_context
from customers.models import Client

from backups.models import Backup, BackupLog
from backups.utils.upload_to_supabase import upload_weekly_backup
from backups.utils.mailer import send_backup_status_email
from backups.utils.alerts import notify_backup_failure


class Command(BaseCommand):
    help = "Run weekly tenant backups and send email notifications"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Starting WEEKLY tenant backups...")

        today = str(timezone.now().date())

        for tenant in Client.objects.exclude(schema_name="public"):
            self.stdout.write(f"📦 Backing up tenant: {tenant.schema_name}")

            backup = Backup.objects.create(
                type=Backup.TENANT,
                tenant_schema=tenant.schema_name,
                #frequency=Backup.WEEKLY,   # 👈 important distinction
                status="running",
                started_at=timezone.now(),
            )

            dump_path = None

            try:
                with schema_context(tenant.schema_name):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".dump") as tmp:
                        dump_path = tmp.name

                    dump_cmd = [
                        "pg_dump",
                        "-Fc",
                        "-n", tenant.schema_name,
                        "-U", settings.DATABASES["default"]["USER"],
                        "-h", settings.DATABASES["default"]["HOST"],
                        "-p", str(settings.DATABASES["default"]["PORT"]),
                        "-d", settings.DATABASES["default"]["NAME"],
                        "-f", dump_path,
                    ]

                    env = os.environ.copy()
                    env["PGPASSWORD"] = settings.DATABASES["default"]["PASSWORD"]

                    result = subprocess.run(
                        dump_cmd,
                        capture_output=True,
                        text=True,
                        env=env,
                    )

                    if result.returncode != 0:
                        raise Exception(result.stderr.strip())

                    # Upload weekly backup
                    uploaded_path = upload_weekly_backup(
                        tenant.schema_name,
                        today,
                        dump_path,
                        subfolder="existing_tenants"
                    )

                    backup.status = "Success"
                    backup.file_path = uploaded_path
                    backup.file_size = os.path.getsize(dump_path)
                    backup.finished_at = timezone.now()
                    backup.save()

                    BackupLog.objects.create(
                        backup=backup,
                        level=BackupLog.LEVEL_INFO,
                        message="Weekly tenant backup completed successfully.",
                    )

                    if tenant.email:
                        send_backup_status_email(
                            to_email=tenant.email,
                            tenant_name=tenant.tenant_name,
                            schema=tenant.schema_name,
                            backup_type="weekly",
                            status="success",
                            file_path=uploaded_path,
                        )

            except Exception as e:
                backup.status = "Failure"
                backup.error_message = str(e)
                backup.finished_at = timezone.now()
                backup.save()

                BackupLog.objects.create(
                    backup=backup,
                    level=BackupLog.LEVEL_ERROR,
                    message=str(e),
                )

                if tenant.email:
                    send_backup_status_email(
                        to_email=tenant.email,
                        tenant_name=tenant.tenant_name,
                        schema=tenant.schema_name,
                        backup_type="weekly",
                        status="failed",
                        error_message=str(e),
                    )

                notify_backup_failure(backup)
                self.stderr.write(f"❌ Weekly backup failed for {tenant.schema_name}: {e}")

            finally:
                if dump_path and os.path.exists(dump_path):
                    os.remove(dump_path)

        self.stdout.write("🎉 WEEKLY tenant backup job finished.")