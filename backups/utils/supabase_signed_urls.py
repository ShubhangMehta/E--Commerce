import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_signed_url(path: str, expires_in: int = 300):
    """
    Generate a signed URL from Supabase Storage.
    """
    try:
        signed = supabase.storage.from_("backups").create_signed_url(
            path=path,
            expires_in=expires_in
        )
        return signed["signedURL"]
    except Exception as e:
        print("Error generating signed URL:", e)
        return None