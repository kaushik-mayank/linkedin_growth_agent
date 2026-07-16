"""Backend-only Supabase client using the service_role key.

Never expose SUPABASE_SERVICE_ROLE_KEY to the frontend — it bypasses row-level
security. The frontend must always go through this backend's API instead.
"""
from supabase import Client, create_client

from app import config

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set — add them to backend/.env"
            )
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    return _client
