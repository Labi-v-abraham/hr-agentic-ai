import streamlit as st
import logging
from typing import Optional
from app.models.user import Profile
from app.database.profile_repository import ProfileRepository
from app.database.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages the Streamlit session state natively.
    No cookies or external packages are used.
    """
    def __init__(self, profile_repository: ProfileRepository, supabase_service: SupabaseService):
        self.profile_repo = profile_repository
        self.supabase_service = supabase_service
        self.client = supabase_service.get_client()

    def persist_session(self, auth_user_id: str, access_token: str, refresh_token: str, expires_at: int) -> bool:
        """Loads profile and persists session state."""
        try:
            profile = self.profile_repo.get_user_by_auth_id(auth_user_id)
            if not profile:
                logger.error(f"Profile not found for auth_id {auth_user_id}")
                return False

            if profile.status != "ACTIVE":
                logger.warning(f"Attempt to persist session for inactive user {profile.email}")
                return False

            # Update last login
            self.profile_repo.update_last_login(auth_user_id)

            # Store only the requested values in st.session_state
            st.session_state.session = {
                "current_user": auth_user_id,
                "profile": profile.model_dump(mode='json'),
                "role": profile.role.value,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at
            }

            logger.info(f"Session persisted in state for {profile.email}")
            return True
        except Exception as e:
            logger.error(f"Error persisting session: {e}")
            return False

    def restore_session(self) -> Optional[dict]:
        """Restores session from st.session_state or attempts auto-login via Supabase native session."""
        # 1. Check if session exists in Streamlit state
        if "session" in st.session_state and st.session_state.session:
            return st.session_state.session

        # 2. Auto-login fallback: Check if Supabase client inherently retained a session
        try:
            sb_session = self.client.auth.get_session()
            if sb_session:
                profile = self.profile_repo.get_user_by_auth_id(sb_session.user.id)
                if profile and profile.status == "ACTIVE":
                    st.session_state.session = {
                        "current_user": sb_session.user.id,
                        "profile": profile.model_dump(mode='json'),
                        "role": profile.role.value,
                        "access_token": sb_session.access_token,
                        "refresh_token": sb_session.refresh_token,
                        "expires_at": sb_session.expires_at
                    }
                    return st.session_state.session
                else:
                    self.logout()
        except Exception as e:
            logger.error(f"Error checking Supabase auto-login: {e}")
            self.logout()
            
        return None

    def logout(self):
        """Clears local session state."""
        if "session" in st.session_state:
            del st.session_state.session
        logger.info("Local session cleared.")

    def get_current_profile(self) -> Optional[Profile]:
        """Returns the Profile model for the currently logged-in user."""
        session = self.restore_session()
        if session and "profile" in session:
            return Profile.model_validate(session["profile"])
        return None
