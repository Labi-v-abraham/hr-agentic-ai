import streamlit as st
import logging
from typing import List
from app.auth.session_manager import SessionManager
from app.models.user import Role

logger = logging.getLogger(__name__)

class AuthorizationService:
    """
    Centralized Authorization Logic.
    Provides middleware functions for Streamlit UI to enforce RBAC.
    """
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def get_current_role(self) -> Role | None:
        profile = self.session_manager.get_current_profile()
        return profile.role if profile else None

    def require_auth(self):
        """Stops execution if the user is not authenticated."""
        if not self.session_manager.get_current_profile():
            st.warning("You must be logged in to view this page.")
            st.stop()

    def require_roles(self, allowed_roles: List[Role]):
        """Stops execution if the user does not have one of the required roles."""
        self.require_auth()
        current_role = self.get_current_role()
        
        if current_role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            st.error(f"Unauthorized Access. This page requires one of the following roles: {', '.join(role_names)}.")
            logger.warning(f"Unauthorized access attempt by role {current_role}. Required: {role_names}")
            st.stop()

    def require_admin(self):
        self.require_roles([Role.HR_ADMIN])

    def require_manager(self):
        self.require_roles([Role.HR_ADMIN, Role.HR_MANAGER])

    # Granular permissions
    def can_upload_documents(self) -> bool:
        return self.get_current_role() in [Role.HR_ADMIN, Role.HR_MANAGER]

    def can_manage_users(self) -> bool:
        return self.get_current_role() == Role.HR_ADMIN

    def can_review_resumes(self) -> bool:
        return self.get_current_role() in [Role.HR_ADMIN, Role.HR_MANAGER]

    def can_view_logs(self) -> bool:
        return self.get_current_role() == Role.HR_ADMIN
