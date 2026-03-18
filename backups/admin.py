from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

#FULL Restore Logic imports.
import os
import tempfile
import requests
import subprocess
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html

from .models import Backup, BackupLog, GlobalBackup
from .utils.supabase_signed_urls import generate_signed_url
from .utils.alerts import notify_backup_failure

#Notifications
from .models import BackupAlert



##########-----
# BackupLogInline class
##########-----
class BackupLogInline(admin.TabularInline):
    model = BackupLog
    extra = 0
    readonly_fields = ("timestamp", "level", "message")
    can_delete = False


##########-----
# BackupAdmin class
##########-----
@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):

    ##############################################
    # ADD THIS LINE FOR CUSTOM DASHBOARD TEMPLATE
    ##############################################
    change_list_template = "admin/backups/change_list_custom.html"

    list_display = (
        "id",
        "type",
        "tenant_schema",
        "created_at",
        "status",
        "download_button",
        "restore_button",
    )

    list_filter = ("type", "status", "tenant_schema")
    search_fields = ("tenant_schema", "file_path")
    readonly_fields = (
        "created_at",
        "started_at",
        "finished_at",
        "file_size",
        "status",
        "error_message",
        "download_button",
    )

    inlines = [BackupLogInline]

    # ---------------------------------------------
    # DOWNLOAD BUTTON
    # ---------------------------------------------
    def download_button(self, obj):
        if not obj.file_path:
            return "No file"

        url = generate_signed_url(path=obj.file_path)
        if not url:
            return "URL Error"

        return format_html(
            '<a class="button" target="_blank" href="{}">Download</a>',
            url,
        )

    download_button.short_description = "Download"

    # ---------------------------------------------
    # RESTORE BUTTON
    # ---------------------------------------------
    def restore_button(self, obj):
        return format_html(
            '<a class="button" href="restore/{}/">Restore</a>',
            obj.id
        )

    restore_button.short_description = "Restore"

    # ---------------------------------------------
    # CUSTOM ADMIN URLs
    # ---------------------------------------------
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "restore/<int:backup_id>/",
                self.admin_site.admin_view(self.restore_backup),
                name="backup-restore",
            ),
            path(
                "stats/",
                self.admin_site.admin_view(self.backup_stats),
                name="backup_stats",
            ),
        ]
        return custom_urls + urls

    # ---------------------------------------------
    # RESTORE LOGIC (YOUR ORIGINAL CODE)
    # ---------------------------------------------
    def restore_backup(self, request, backup_id):
        if not request.user.is_superuser:
            self.message_user(request, "Only superusers can restore backups!", level=messages.ERROR)
            return redirect("..")

        backup = Backup.objects.get(id=backup_id)

        signed_url = generate_signed_url(backup.file_path)
        if not signed_url:
            messages.error(request, "Failed to generate signed URL for restore.")
            return redirect("..")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".dump")
        response = requests.get(signed_url)

        if response.status_code != 200:
            messages.error(request, "Failed to download backup file.")
            return redirect("..")

        temp_file.write(response.content)
        temp_file.close()

        try:
            restore_cmd = [
                "pg_restore",
                "-U", settings.DATABASES["default"]["USER"],
                "-h", settings.DATABASES["default"]["HOST"],
                "-d", backup.tenant_schema,
                temp_file.name,
            ]

            process = subprocess.run(
                restore_cmd,
                capture_output=True,
                text=True,
                env={"PGPASSWORD": settings.DATABASES["default"]["PASSWORD"]},
            )

            if process.returncode != 0:
                backup.status = "failed"
                backup.error_message = process.stderr
                backup.save()

                BackupLog.objects.create(
                    backup=backup,
                    status="restore_failed",
                    error_message=process.stderr,
                )

                send_backup_failure_alert(backup, process.stderr)

                messages.error(request, f"Restore failed: {process.stderr}")
                return redirect("..")

            BackupLog.objects.create(
                backup=backup,
                status="restored",
                message="Database restored successfully",
            )

            messages.success(request, "Backup restored successfully!")
            return redirect("..")

        except Exception as e:
            backup.status = "failed"
            backup.error_message = str(e)
            backup.save()

            BackupLog.objects.create(
                backup=backup,
                status="restore_failed",
                error_message=str(e),
            )

            send_backup_failure_alert(backup, str(e))

            messages.error(request, f"Restore failed: {str(e)}")
            return redirect("..")

    # ---------------------------------------------
    # 📊 BACKUP STATISTICS DASHBOARD (ADDED)
    # ---------------------------------------------
    def backup_stats(self, request):
        success_count = Backup.objects.filter(status="success").count()
        failed_count = Backup.objects.filter(status="failed").count()

        last_7_days = timezone.now() - timedelta(days=7)

        backup_trend = (
            Backup.objects.filter(created_at__gte=last_7_days)
            .extra(select={'day': "date(created_at)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        context = {
            "title": "Backup Statistics",
            "success_count": success_count,
            "failed_count": failed_count,
            "trend": list(backup_trend),
        }

        return TemplateResponse(request, "admin/backup_stats.html", context)


#admin.site.register(Backup, BackupAdmin)


##########-----
# GlobalBackupAdmin class
##########-----
@admin.register(GlobalBackup)
class GlobalBackupAdmin(admin.ModelAdmin):
    list_display = ("backup", "retention_weeks", "created_at")
    readonly_fields = ("backup", "retention_weeks", "created_at")



from django.contrib import admin
from .models import BackupAlert


@admin.register(BackupAlert)
class BackupAlertAdmin(admin.ModelAdmin):
    list_display = ("backup", "retention_weeks", "created_at")
    list_filter = ("retention_weeks",)

    search_fields = ("backup__tenant", "backup__date", "error_message")

    def tenant(self, obj):
        return obj.backup.tenant
    tenant.admin_order_field = "backup__tenant"

    def date(self, obj):
        return obj.backup.date
    date.admin_order_field = "backup__date"