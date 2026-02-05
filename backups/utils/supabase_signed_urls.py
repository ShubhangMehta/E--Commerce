# backups/utils/supabase_signed_urls.py
from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/Users/sasiabburi/E--Commerce/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "backups")  # default 'backups'

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_signed_url(file_path: str, expiry: int = 3600) -> str:
    """
    Generate a signed URL for a file in Supabase storage.
    
    file_path: path inside Supabase bucket, e.g., 'tenants/daily/2025-12-08/tenant1.dump'
    expiry: expiration in seconds
    """
    try:
        # Ensure bucket path is correct
        signed_url_data = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(file_path, expiry)
        return signed_url_data["signedUrl"]
    except Exception as e:
        print("Error generating signed URL:", e)
        return None