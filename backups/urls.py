from django.urls import path
from . import views

urlpatterns = [
    path("", views.backups, name="backups_home"),

    # API endpoints
    path("generate-daily-backup-link/", views.generate_backup_link_daily, name="generate_backup_link_daily"),
    path("generate-weekly-backup-link/", views.generate_backup_link_weekly, name="generate_backup_link_weekly"),
    path("generate-master-backup-link/", views.generate_backup_link_master, name="generate_backup_link_master"),

    # Downloads
    path("downloads/", views.download_backups, name="download_backups"),
    path("downloads/daily/", views.daily_backups_view, name="daily_backups_view"),
    path("downloads/weekly/", views.weekly_backups_view, name="weekly_backups_view"),
    path("downloads/master/", views.master_backups_view, name="master_backups_view"),

    # Restore
    path("restore/", views.restore_backups, name="restore_backups"),
    path("restore-api/", views.restore_backup_api, name="restore_backup_api"),

    # Stats
    path("stats/", views.backup_stats, name="backup_stats"),
]