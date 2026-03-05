import sys
import os
import tempfile
from supabase import create_client, Client

# Load Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -------------------------------------------------------------
# DAILY BACKUP UPLOAD
# -------------------------------------------------------------
def upload_daily_backup(schema: str, date: str, temp_file_path: str):
    file_name = f"{schema}-daily.dump"
    bucket_path = f"tenants/daily/{date}/{file_name}"

    print(f"⬆️ Uploading DAILY backup → {bucket_path}")

    supabase.storage.from_("backups").upload(
        path=bucket_path,
        file=temp_file_path,
        file_options={"content-type": "application/octet-stream"},
    )

    print(f"✅ DAILY upload complete → {bucket_path}")


# -------------------------------------------------------------
# WEEKLY BACKUP UPLOAD
# -------------------------------------------------------------
def upload_weekly_backup(schema: str, date: str, temp_file_path: str):
    file_name = f"{schema}-weekly.dump"
    bucket_path = f"tenants/weekly/{date}/{file_name}"

    print(f"⬆️ Uploading WEEKLY backup → {bucket_path}")

    supabase.storage.from_("backups").upload(
        path=bucket_path,
        file=temp_file_path,
        file_options={"content-type": "application/octet-stream"},
    )

    print(f"✅ WEEKLY upload complete → {bucket_path}")


# -------------------------------------------------------------
# MASTER BACKUP UPLOAD
# -------------------------------------------------------------
def upload_master_backup(schema: str, date: str, temp_file_path: str):
    file_name = f"master-{date}.dump"
    bucket_path = f"tenants/master/{date}/{file_name}"

    print(f"⬆️ Uploading MASTER backup → {bucket_path}")

    supabase.storage.from_("backups").upload(
        path=bucket_path,
        file=temp_file_path,
        file_options={"content-type": "application/octet-stream"},
    )

    print(f"✅ MASTER upload complete → {bucket_path}")


# -------------------------------------------------------------
# MAIN HANDLER
# -------------------------------------------------------------
if __name__ == "__main__":
    # sys.argv:
    #   1 → schema
    #   2 → date
    #   3 → mode: daily | weekly | master

    if len(sys.argv) < 4:
        print("❌ Usage: python upload_to_supabase.py <schema> <date> <mode>")
        sys.exit(1)

    schema = sys.argv[1]
    date = sys.argv[2]
    mode = sys.argv[3].lower()

    # Read streamed pg_dump output → temp file
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(sys.stdin.buffer.read())
    temp.flush()

    # Decide upload target
    if mode == "daily":
        upload_daily_backup(schema, date, temp.name)

    elif mode == "weekly":
        upload_weekly_backup(schema, date, temp.name)

    elif mode == "master":
        upload_master_backup(schema, date, temp.name)

    else:
        print("❌ Invalid mode! Choose: daily | weekly | master")
        sys.exit(1)

    # Clean temp file
    temp.close()
    os.unlink(temp.name)