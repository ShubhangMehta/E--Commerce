from django.urls import path
from . import views

app_name = "backups"

urlpatterns = [
    # ===== UI PAGES =====
    path("", views.backups, name="backups"),

    path("downloads/", views.download_backups, name="downloads"),
    path("downloads/daily/", views.daily_backups_view, name="daily"),
    path("downloads/weekly/", views.weekly_backups_view, name="weekly"),
    path("downloads/master/", views.master_backups_view, name="master"),

    path("restore/", views.restore_backups, name="restore"),
    path("stats/", views.backup_stats, name="stats"),

    # ===== API ENDPOINTS =====
    path("api/generate/daily/", views.generate_backup_link_daily, name="api_generate_daily"),
    path("api/generate/weekly/", views.generate_backup_link_weekly, name="api_generate_weekly"),
    path("api/generate/master/", views.generate_backup_link_master, name="api_generate_master"),

    path("api/restore/", views.restore_backup_api, name="api_restore"),

    # optional (manual trigger)
    path("api/trigger/", views.trigger_backup, name="api_trigger"),
]