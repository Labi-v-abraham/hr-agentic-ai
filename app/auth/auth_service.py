import logging
from typing import Tuple
from app.database.supabase_service import SupabaseService
from app.auth.session_manager import SessionManager

logger = logging.getLogger(__name__)

class AuthService:
    """
    Handles authentication flows using Supabase Auth.
    Strictly decoupled from Profile table logic (which is handled post-login by SessionManager).
    """
    def __init__(self, supabase_service: SupabaseService, session_manager: SessionManager):
        self.supabase_service = supabase_service
        self.session_manager = session_manager
        self.client = supabase_service.get_client()

    def login(self, email: str, password: str) -> Tuple[bool, str]:
        """Authenticates user via Supabase and persists session via SessionManager."""
        try:
            res = self.client.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                # Auth succeeded. Now SessionManager loads profile and handles state.
                success = self.session_manager.persist_session(
                    auth_user_id=res.user.id,
                    access_token=res.session.access_token,
                    refresh_token=res.session.refresh_token,
                    expires_at=res.session.expires_at
                )
                if success:
                    logger.info(f"User {email} logged in successfully.")
                    return True, "Login successful."
                else:
                    self.client.auth.sign_out()
                    return False, "Failed to load user profile or account is inactive."
            return False, "Unknown error during login."
        except Exception as e:
            logger.error(f"Login failed for {email}: {e}")
            if "Invalid login credentials" in str(e):
                return False, "Invalid email or password."
            elif "Email not confirmed" in str(e):
                return False, "Email not confirmed. Please check your inbox or contact admin."
            return False, f"Login error: {str(e)}"

    def logout(self):
        """Signs out of Supabase and clears local session."""
        try:
            self.client.auth.sign_out()
        except Exception as e:
            logger.error(f"Error signing out of Supabase: {e}")
        finally:
            self.session_manager.logout()
