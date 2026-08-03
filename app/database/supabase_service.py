import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseService:
    """
    Centralized Supabase Service for managing clients and connection.
    Implements a Singleton pattern to avoid recreating clients.
    """
    _instance: Optional["SupabaseService"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SupabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.url = os.getenv("SUPABASE_URL")
            self.anon_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
            self.service_role_key = os.getenv("SUPABASE_SERVICE_KEY")

            if not self.url or not self.anon_key:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")

            # Main anon client for auth and general operations
            self._client = create_client(self.url, self.anon_key)
            
            # Elevated client for backend admin tasks (bypasses RLS)
            if self.service_role_key:
                self._admin_client = create_client(self.url, self.service_role_key)
            else:
                self._admin_client = None

            self.initialized = True
            logger.info("SupabaseService initialized successfully.")

    def get_client(self) -> Client:
        """Returns the standard anon client."""
        return self._client

    def get_admin_client(self) -> Client:
        """Returns the service role client. Falls back to anon client if service role is not set."""
        if self._admin_client:
            return self._admin_client
        logger.warning("SUPABASE_SERVICE_KEY not set. Falling back to anon client for admin operations.")
        return self._client

    def insert_evaluation(self, evaluation_data: dict) -> bool:
        """Insert a resume evaluation into the evaluations table."""
        try:
            res = self.get_admin_client().table("evaluations").insert(evaluation_data).execute()
            if res.data:
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to insert evaluation: {e}")
            return False
