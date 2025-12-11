from django.urls import path
from . import views     # <-- THIS WAS MISSING

urlpatterns = [
    #Backup application path
    path("", views.backups, name="backups_home"),

    #Downloading backups path
    #path("download/", views.download_backups, name="download_backups"),
    path("generate-daily-backup-link/", views.generate_backup_link_daily, name="generate_backup_link"),
    path("backups/downloads/", views.download_backups, name="download_backups"), 
    path("backups/downloads/daily/", views.daily_backups_view, name="daily_backups_view"),
    path("backups/downloads/weekly/", views.weekly_backups_view, name="weekly_backups_view"),
    path("backups/downloads/master/", views.master_backups_view, name="master_backups_view"),


    #Restore Paths
    path("restore/", views.restore_backups, name="restore_backups"),
    path("restore-api/", views.restore_backup_api, name="restore_backup_api"),


    path("stats/", views.backup_stats, name="backup_stats"),
]