import os
import tempfile
import subprocess
from django.shortcuts import redirect
from django.http import HttpResponse
from .utils import supabase_signed_urls
from django.http import JsonResponse
from backups.utils.supabase_signed_urls import generate_signed_url
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from backups.utils.supabase_signed_urls import supabase
from supabase import create_client, Client
from .utils.alerts import notify_backup_failure
from django.utils import timezone


#######-----
#Main backup template
#######-----
def backups(request):
    return render(request, "backups/backups.html")

#####----
#Download backups templates starts
#####----
def download_backups(request):
    return render(request, "backups/download_backups.html")


def daily_backups_view(request):
    return render(request, "backups/daily_backups.html")

def weekly_backups_view(request):
    return render(request, "backups/weekly_backups.html")

def master_backups_view(request):
    return render(request, "backups/master_backups.html")
#####----
#Download backups templates ends
#####----

def restore_backups(request):
    return render(request, "backups/restore_backups.html")

def backup_stats(request):
    return render(request, "backups/backup_stats.html")


def make_aware_safe(dt):
    if dt is None:
        return None
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt




######------
# signed_urls_for_daily
######------
@csrf_exempt
def generate_backup_link_daily(request):
    if request.method == "POST":
        tenant = request.POST.get("tenant")
        date = request.POST.get("date")

        if not tenant or not date:
            return JsonResponse({"error": "Missing tenant or date"}, status=400)

        # Supabase file path structure
        file_path = f"tenants/daily/{date}/{tenant}.dump"

        url = generate_signed_url(file_path)

        if not url:
            return JsonResponse({"error": "Backup file not found"}, status=404)

        return JsonResponse({"url": url})

    return JsonResponse({"error": "Invalid request method"}, status=405)


######------
# signed_urls_for_weekly
######------

@csrf_exempt
def generate_backup_link_weekly(request):
    if request.method == "POST":
        tenant = request.POST.get("tenant")
        date = request.POST.get("date")

        if not tenant or not date:
            return JsonResponse({"error": "Missing tenant or date"}, status=400)

        # Supabase file path structure
        file_path = f"tenants/weekly/{date}/{tenant}.dump"

        url = generate_signed_url(file_path)

        if not url:
            return JsonResponse({"error": "Backup file not found"}, status=404)

        return JsonResponse({"url": url})

    return JsonResponse({"error": "Invalid request method"}, status=405)


######------
# signed_urls_for_master
######------

@csrf_exempt
def generate_backup_link_master(request):
    if request.method == "POST":
        tenant = request.POST.get("tenant")
        date = request.POST.get("date")

        if not tenant or not date:
            return JsonResponse({"error": "Missing tenant or date"}, status=400)

        # Supabase file path structure
        file_path = f"tenants/master/{date}/{tenant}.dump"

        url = generate_signed_url(file_path)

        if not url:
            return JsonResponse({"error": "Backup file not found"}, status=404)

        return JsonResponse({"url": url})

    return JsonResponse({"error": "Invalid request method"}, status=405)


######------
# restore logic
######------


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@csrf_exempt
def restore_backup_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    tenant = request.POST.get("tenant")
    date = request.POST.get("date")

    if not tenant or not date:
        return JsonResponse({"error": "Missing tenant or date"}, status=400)

    file_path = f"tenants/daily/{date}/{tenant}.dump"

    # Step 1: download file
    try:
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        res = supabase.storage.from_("backups").download(file_path)
        if isinstance(res, bytes):
            tmp_file.write(res)
        elif isinstance(res, dict) and "content" in res:
            tmp_file.write(res["content"])
        else:
            raise Exception("File not found in storage")
        tmp_file.close()
    except Exception as e:
        notify_backup_failure(tenant, date, str(e))
        return JsonResponse({"error": f"Download failed → {e}"}, status=500)

    # Step 2: restore safely
    try:
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT") or "5432"

        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD

        command = [
            "pg_restore",
            "--no-owner",       # don’t try to set ownership
            "--no-privileges",  # skip GRANT commands
            "--clean",          # drop objects before recreating
            "--if-exists",      # only drop if they exist
            "--dbname=postgresql://{}@{}:{}/{}".format(DB_USER, DB_HOST, DB_PORT, DB_NAME),
            tmp_file.name
        ]

        subprocess.check_output(command, stderr=subprocess.STDOUT, env=env)

    except subprocess.CalledProcessError as e:
        notify_backup_failure(tenant, date, e.output.decode())
        return JsonResponse({"error": e.output.decode()}, status=500)

    finally:
        if os.path.exists(tmp_file.name):
            os.remove(tmp_file.name)

    # Step 3: delete file from storage
    try:
        supabase.storage.from_("backups").remove([file_path])
    except Exception as e:
        notify_backup_failure(tenant, date, f"Restore OK but delete failed → {str(e)}")

    return JsonResponse({"status": "success", "message": "Backup restored successfully"})



######-----
#Notifications
######-----
from .services import generate_backup_for_tenant

def trigger_backup(request):
    tenant = request.user.tenant
    result = generate_backup_for_tenant(tenant, "daily")
    return JsonResponse(result)