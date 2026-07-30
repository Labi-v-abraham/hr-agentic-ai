import logging
from typing import Tuple, List
from app.database.supabase_service import SupabaseService
from app.database.profile_repository import ProfileRepository
from app.models.user import Profile

logger = logging.getLogger(__name__)

class UserService:
    """
    Business logic for managing users. 
    Typically used by HR_ADMIN via the Admin Dashboard.
    """
    def __init__(self, supabase_service: SupabaseService, profile_repository: ProfileRepository):
        self.supabase_service = supabase_service
        self.profile_repo = profile_repository
        # Need admin client to create users directly without logging in as them
        self.admin_client = supabase_service.get_admin_client()

    def create_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Creates a new user via Supabase Auth Admin API (if service role is available) or signup."""
        try:
            # If using Service Role, we can use the admin API which bypasses email confirmations.
            # If we don't have it (fallback to anon), we use sign_up.
            if self.supabase_service.service_role_key:
                res = self.admin_client.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True
                })
                if res.user:
                    logger.info(f"User {email} created via Admin API.")
                    return True, "User created successfully."
            else:
                # Fallback to anon sign_up
                current_session = self.admin_client.auth.get_session()
                res = self.admin_client.auth.sign_up({"email": email, "password": password})
                if current_session:
                    self.admin_client.auth.set_session(current_session.access_token, current_session.refresh_token)
                
                if res.user:
                    logger.info(f"User {email} created via anon sign_up.")
                    return True, "User created. (Note: Email confirmation may be required depending on Supabase settings)."
                    
            return False, "Failed to create user."
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return False, str(e)

    def get_all_users(self) -> List[Profile]:
        return self.profile_repo.get_all_profiles()

    def change_user_role(self, auth_user_id: str, new_role: str) -> bool:
        return self.profile_repo.update_role(auth_user_id, new_role)
