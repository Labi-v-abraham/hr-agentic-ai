import logging
from typing import Optional, List
from app.database.supabase_service import SupabaseService
from app.models.user import Profile

logger = logging.getLogger(__name__)

class ProfileRepository:
    """
    Handles all database operations related to the `profiles` table.
    """
    def __init__(self, supabase_service: SupabaseService):
        self.supabase_service = supabase_service
        # We use the admin client because RLS is disabled on profiles
        # and we manage access exclusively through this backend service.
        self.client = supabase_service.get_admin_client()

    def get_user_by_auth_id(self, auth_user_id: str) -> Optional[Profile]:
        try:
            response = self.client.table("profiles").select("*").eq("auth_user_id", auth_user_id).execute()
            if response.data and len(response.data) > 0:
                return Profile.model_validate(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching profile for auth_id {auth_user_id}: {e}")
            return None

    def get_all_profiles(self) -> List[Profile]:
        try:
            response = self.client.table("profiles").select("*").execute()
            return [Profile.model_validate(p) for p in response.data]
        except Exception as e:
            logger.error(f"Error fetching all profiles: {e}")
            return []

    def update_role(self, auth_user_id: str, new_role: str) -> bool:
        try:
            response = self.client.table("profiles").update({"role": new_role}).eq("auth_user_id", auth_user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error updating role for auth_id {auth_user_id}: {e}")
            return False

    def update_last_login(self, auth_user_id: str) -> bool:
        try:
            response = self.client.table("profiles").update({"last_login": "now()"}).eq("auth_user_id", auth_user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error updating last login for auth_id {auth_user_id}: {e}")
            return False
