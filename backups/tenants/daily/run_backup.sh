import subprocess
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Run database backup and notify admin if it fails"

    def handle(self, *args, **kwargs):
        script_path = "/Users/sasiabburi/E--Commerce/scripts/daily_backup"

        result = subprocess.run([script_path], shell=True)
        if result.returncode != 0:
            send_mail(
                subject="Backup Failed",
                message=f"Backup script {script_path} failed. Manual action required.",
                from_email="admin@yourdomain.com",
                recipient_list=["admin@yourdomain.com"],
            )
            self.stdout.write(self.style.ERROR("Backup failed — admin notified."))
        else:
            self.stdout.write(self.style.SUCCESS("Backup completed successfully."))