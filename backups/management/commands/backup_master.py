import os
import subprocess
import tempfile
from django.core.management.base import BaseCommand
from django.utils import timezone

from backups.models import Backup, BackupLog
from backups.utils.supabase_upload import upload_backup_file
from backups.utils.alerts import send_backup_failure_alert

from django.conf import settings


class Command(BaseCommand):
    help = "Create a master (global) backup of the entire database"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Starting Master DB Backup...")

        # 1. Create DB backup record
        backup = Backup.objects.create(
            type=Backup.GLOBAL,
            tenant_schema=None,
            status="running",
            started_at=timezone.now(),
        )

        try:
            # 2. Create a temporary dump file
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

            # ❌ Dump failed
            if process.returncode != 0:
                backup.status = "failed"
                backup.error_message = process.stderr
                backup.finished_at = timezone.now()
                backup.save()

                BackupLog.objects.create(
                    backup=backup,
                    level=BackupLog.LEVEL_ERROR,
                    message=f"Master backup failed: {process.stderr}",
                )

                send_backup_failure_alert(backup, process.stderr)

                return self.stdout.write(self.style.ERROR("❌ Master backup FAILED."))

            # 3. Upload dump to Supabase
            file_path = f"master/{timezone.now().strftime('%Y-%m-%d_%H-%M')}.dump"
            uploaded_path = upload_backup_file(temp_dump.name, file_path)

            backup.file_path = uploaded_path
            backup.status = "success"
            backup.finished_at = timezone.now()
            backup.file_size = os.path.getsize(temp_dump.name)
            backup.save()

            BackupLog.objects.create(
                backup=backup,
                level=BackupLog.LEVEL_INFO,
                message="Master backup completed successfully.",
            )

            self.stdout.write(self.style.SUCCESS("✅ Master backup DONE!"))

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

            send_backup_failure_alert(backup, str(e))

            self.stdout.write(self.style.ERROR(f"❌ Master backup ERROR: {e}"))