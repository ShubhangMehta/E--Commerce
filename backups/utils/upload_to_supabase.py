import sys
import os
import tempfile
from supabase import create_client, Client

# -------------------------------------------------------------
# Load Supabase credentials
# -------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET = "backups"


# -------------------------------------------------------------
# DAILY BACKUP UPLOAD
# -------------------------------------------------------------
def upload_daily_backup(schema: str, date: str, temp_file_path: str, subfolder: str):
    file_name = f"{schema}.dump"
    bucket_path = f"tenants/daily/{date}/{subfolder}/{file_name}"

    print(f"⬆️ Uploading DAILY → {bucket_path}")

    supabase.storage.from_(BUCKET).upload(
        path=bucket_path,
        file=temp_file_path,
        file_options={"content-type": "application/octet-stream"},
    )

    print("✅ DAILY upload complete")


# -------------------------------------------------------------
# WEEKLY BACKUP UPLOAD
# -------------------------------------------------------------
def upload_weekly_backup(schema: str, date: str, temp_file_path: str, subfolder: str):
    file_name = f"{schema}.dump"
    bucket_path = f"tenants/weekly/{date}/{subfolder}/{file_name}"

    print(f"⬆️ Uploading WEEKLY → {bucket_path}")

    supabase.storage.from_(BUCKET).upload(
        path=bucket_path,
        file=temp_file_path,
        file_options={"content-type": "application/octet-stream"},
    )

    print("✅ WEEKLY upload complete")


# -------------------------------------------------------------
# MASTER BACKUP UPLOAD (UNCHANGED)
# -------------------------------------------------------------
def upload_master_backup(date: str, temp_file_path: str):
    file_name = f"master-{date}.dump"
    bucket_path = f"tenants/master/{date}/{file_name}"

    print(f"⬆️ Uploading MASTER → {bucket_path}")

    supabase.storage.from_(BUCKET).upload(
        path=bucket_path,
        file=temp_file_path,
        file_options={"content-type": "application/octet-stream"},
    )

    print("✅ MASTER upload complete")


# -------------------------------------------------------------
# MAIN HANDLER
# -------------------------------------------------------------
if __name__ == "__main__":
    """
    Usage:
      python upload_to_supabase.py <schema> <date> <mode> [subfolder]

    mode       : daily | weekly | master
    subfolder  : existing_tenants | all_tenants (optional)
    """

    if len(sys.argv) < 4:
        print("❌ Usage: python upload_to_supabase.py <schema> <date> <mode> [subfolder]")
        sys.exit(1)

    schema = sys.argv[1]
    date = sys.argv[2]
    mode = sys.argv[3].lower()

    # Optional subfolder (default = existing_tenants)
    subfolder = sys.argv[4] if len(sys.argv) >= 5 else "existing_tenants"

    # Read piped pg_dump into temp file
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(sys.stdin.buffer.read())
    temp.flush()

    try:
        if mode == "daily":
            upload_daily_backup(schema, date, temp.name, subfolder)

        elif mode == "weekly":
            upload_weekly_backup(schema, date, temp.name, subfolder)

        elif mode == "master":
            upload_master_backup(date, temp.name)

        else:
            raise ValueError("Invalid mode: choose daily | weekly | master")

    finally:
        temp.close()
        os.unlink(temp.name)