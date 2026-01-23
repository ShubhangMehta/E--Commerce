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
from backups.utils.alerts import notify_backup_failure


class Command(BaseCommand):
    help = "Run daily tenant backups and send instant email notifications"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Starting DAILY tenant backups...")

        today = str(timezone.now().date())

        for tenant in Client.objects.exclude(schema_name="public"):
            self.stdout.write(f"📦 Backing up tenant: {tenant.schema_name}")

            backup = Backup.objects.create(
            type=Backup.TENANT,
            tenant_schema=tenant.schema_name,
            status="running",
            started_at=timezone.now(),
            )

            try:
                with schema_context(tenant.schema_name):
                    # Create temp dump file
                    file_name = f"{tenant.schema_name}-daily.dump"
                    dump_path = os.path.join(tempfile.gettempdir(), file_name)

                    dump_cmd = [
                        "pg_dump",
                        "-Fc",
                        "-n", tenant.schema_name,   # ⭐ IMPORTANT
                        "-U", settings.DATABASES["default"]["USER"],
                        "-h", settings.DATABASES["default"]["HOST"],
                        "-p", str(settings.DATABASES["default"]["PORT"]),
                        "-d", settings.DATABASES["default"]["NAME"],
                        "-f", dump_path,
                        ]

                    env = os.environ.copy()
                    env["PGPASSWORD"] = settings.DATABASES["default"]["PASSWORD"]

                    process = subprocess.run(
                        dump_cmd,
                        capture_output=True,
                        text=True,
                        env=env,
                    )

                    if process.returncode != 0:
                        raise Exception(process.stderr.strip())

                    # Upload to Supabase
                    uploaded_path = upload_daily_backup(
                        tenant.schema_name,
                        today,
                        dump_path,
                        subfolder="existing_tenants"
                    )

                    # Update backup record
                    backup.status = "Success"
                    backup.file_path = uploaded_path
                    backup.file_size = os.path.getsize(dump_path)
                    backup.finished_at = timezone.now()
                    backup.save()

                    BackupLog.objects.create(
                        backup=backup,
                        level=BackupLog.LEVEL_INFO,
                        message="Daily tenant backup completed successfully.",
                    )

                    # ✅ SUCCESS EMAIL
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
                backup.status = "Failure"
                backup.error_message = str(e)
                backup.finished_at = timezone.now()
                backup.save()

                BackupLog.objects.create(
                    backup=backup,
                    level=BackupLog.LEVEL_ERROR,
                    message=str(e),
                )

                # ❌ FAILURE EMAIL
                if tenant.email:
                    send_backup_status_email(
                        to_email=tenant.email,
                        tenant_name=tenant.tenant_name,
                        schema=tenant.schema_name,
                        backup_type="daily",
                        status="failed",
                        error_message=str(e),
                    )

                notify_backup_failure(backup)
                self.stderr.write(f"❌ Backup failed for {tenant.schema_name}: {e}")

            finally:
                # Cleanup temp file
                try:
                    if os.path.exists(dump_path):
                        os.remove(dump_path)
                except Exception:
                    pass

        self.stdout.write("🎉 DAILY tenant backup job finished.")